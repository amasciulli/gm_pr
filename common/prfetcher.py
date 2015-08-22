#
# Copyright 2015 Genymobile
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from celery import group, subtask
from operator import attrgetter
import re

from django.utils import dateparse
from django.utils import timezone

from common import paginablejson, models
from gm_pr.celery import app
from web.models import ProjectRepository, GeneralSettings, FeedbackGithub, LabelGithub

def is_color_light(rgb_hex_color_string):
    """ return true if the given html hex color string is a "light" color
    https://en.wikipedia.org/wiki/Relative_luminance
    """
    r, g, b = rgb_hex_color_string[:2], rgb_hex_color_string[2:4], \
              rgb_hex_color_string[4:]
    r, g, b = [int(n, 16) for n in (r, g, b)]
    y = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)

    return y > 128

def parse_githubdata(data):
    """
    data { 'repo': genymotion-libauth,
           detail: paginable,
          label: paginable,
          comment: paginable,
          json: json} }
    return models.Pr
    """
    general_settings = GeneralSettings.objects.first()
    old_period = general_settings.old_period
    feedback_ok_sym = FeedbackGithub.objects.filter(general_settings=general_settings, type="ok").first().name
    feedback_weak_sym = FeedbackGithub.objects.filter(general_settings=general_settings, type="weak").first().name
    feedback_ko_sym = FeedbackGithub.objects.filter(general_settings=general_settings, type="ko").first().name
    old_labels = LabelGithub.objects.filter(general_settings=general_settings).all()
    feedback_ok = 0
    feedback_weak = 0
    feedback_ko = 0
    milestone = data['json']['milestone']
    labels = list()
    now = timezone.now()
    for lbl in data['label']:
        label_style = 'light' if is_color_light(lbl['color']) else 'dark'
        labels.append({'name' : lbl['name'],
                       'color' : lbl['color'],
                       'style' : label_style,
        })

    date = dateparse.parse_datetime(data['json']['updated_at'])
    is_old = False
    if (now - date).days >= old_period:
        if not labels and None in old_labels:
            is_old = True
        else:
            for lbl in labels:
                if lbl['name'] in old_labels:
                    is_old = True
                    break

    # FIXME: iterating on a PaginableJson can result in a http request (if there
    # is more than one page). Here the request will be done in the django
    # process and will not be parallelised.

    # look for tags only in main conversation and not in "file changed"
    for jcomment in data['comment']:
        body = jcomment['body']
        if re.search(feedback_ok_sym, body):
            feedback_ok += 1
        if re.search(feedback_weak_sym, body):
            feedback_weak += 1
        if re.search(feedback_ko_sym, body):
            feedback_ko += 1
    if milestone:
        milestone = milestone['title']

    pr = models.Pr(url=data['json']['html_url'],
                   title=data['json']['title'],
                   updated_at=date,
                   user=data['json']['user']['login'],
                   repo=data['json']['base']['repo']['name'],
                   nbreview=int(data['detail']['comments']) +
                            int(data['detail']['review_comments']),
                   feedback_ok=feedback_ok,
                   feedback_weak=feedback_weak,
                   feedback_ko=feedback_ko,
                   milestone=milestone,
                   labels=labels,
                   is_old=is_old)
    return pr

@app.task
def get_urls_for_repo(repo_name, url, org):
    url = "%s/repos/%s/%s/pulls" % (url, org, repo_name)
    json_prlist = paginablejson.PaginableJson(url)
    tagurls = []
    if not json_prlist:
        return tagurls
    for json_pr in json_prlist:
        if json_pr['state'] == 'open':
            tagurls.append({ 'repo' : repo_name,
                          'tag' : 'json',
                          'prid' : json_pr['id'],
                          # XXX: this is not a url. We pass the json to have it
                          # the final data response. see get_tagdata_from_url
                          'url' : json_pr })
            tagurls.append({ 'repo' : repo_name,
                          'tag' : 'comment',
                          'prid' : json_pr['id'],
                          'url' : json_pr['comments_url'] })
            tagurls.append({ 'repo' : repo_name,
                          'tag' : 'detail',
                          'prid' : json_pr['id'],
                          'url' : json_pr['url'] })
            tagurls.append({ 'repo' : repo_name,
                          'tag' : 'label',
                          'prid' : json_pr['id'],
                          'url' : "%s/labels" % json_pr['issue_url'] })

    return tagurls

@app.task
def dmap(it, callback):
    # http://stackoverflow.com/questions/13271056/how-to-chain-a-celery-task-that-returns-a-list-into-a-group
    # Map a callback over an iterator and return as a group
    callback = subtask(callback)
    return group(callback.clone((arg,)) for arg in it)()

@app.task
def get_tagdata_from_url(tagurl):
    if tagurl['tag'] == 'json':
        return { 'repo' : tagurl['repo'],
                 'tag' : tagurl['tag'],
                 'prid' : tagurl['prid'],
                 'json' : tagurl['url']}
    else:
        return { 'repo' : tagurl['repo'],
                 'tag' : tagurl['tag'],
                 'prid' : tagurl['prid'],
                 'json' : paginablejson.PaginableJson(tagurl['url'])}

class PrFetcher:
    """ Pr fetcher
    """
    def __init__(self, url, org, repos):
        """
        url -- top level url (eg: https://api.github.com)
        org -- github organisation (eg: Genymobile)
        repos -- repo name (eg: gm_pr)
        """
        self.__url = url
        self.__org = org
        self.__repos = repos

    def get_prs(self):
        """
        fetch the prs from github

        return a list of { 'name' : repo_name, 'pr_list' : pr_list }
        pr_list is a list of models.Pr
        """
        # { 41343736 : { 'repo': genymotion-libauth,
        #                detail: paginable,
        #                label: paginable,
        #                comment: paginable } }
        github_data = {}
        res = group((get_urls_for_repo.s(repo_name, self.__url, self.__org) | \
                     dmap.s(get_tagdata_from_url.s()))
                    for repo_name in self.__repos)()
        for groupres in res.get():
            for tagdata in groupres.get():
                prid = tagdata['prid']
                if prid not in github_data:
                    github_data[prid] = {}
                    github_data[prid]['repo'] = tagdata['repo']
                github_data[prid][tagdata['tag']] = tagdata['json']

        prlist = [ parse_githubdata(github_data[prid]) for prid in github_data ]
        repo_pr = {}
        for pr in prlist:
            if pr.repo not in repo_pr:
                repo_pr[pr.repo] = []
            repo_pr[pr.repo].append(pr)

        return repo_pr
