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

# Create your views here.


import time

from django.shortcuts import render

from django.http import HttpResponse

from common import proj_repo
from common.prfetcher import PrFetcher
from web.models import ProjectRepository, GeneralSettings, FeedbackGithub, LabelGithub


def index(request):
    general_settings = GeneralSettings.objects.first()

    if not general_settings:
        return HttpResponse("No configurations found\n", status=404)

    if not request.GET:
        project_list = ProjectRepository.objects.filter(parent=None, general_settings=general_settings)
        context = {'title': "Project list",
                   'project_list': project_list}
        return render(request, 'index.html', context)

    project, repos = proj_repo.proj_repo(request)

    if repos:
        before = time.time()
        feedback_ok = FeedbackGithub.objects.filter(general_settings=general_settings, type="ok").first()
        feedback_weak = FeedbackGithub.objects.filter(general_settings=general_settings, type="weak").first()
        feedback_ko = FeedbackGithub.objects.filter(general_settings=general_settings, type="ko").first()
        label_github = LabelGithub.objects.filter(general_settings=general_settings)

        prf = PrFetcher(general_settings.top_level_url, general_settings.organization,
                        #general_settings.old_period, label_github,
                        #feedback_ok.keyword,
                        #feedback_weak.keyword,
                        #feedback_ko.keyword,
                        repos)
        context = {"title" : "%s PR list" % project,
                   "projects" : prf.get_prs(),
                   "feedback_ok" : feedback_ok.name,
                   "feedback_weak" : feedback_weak.name,
                   "feedback_ko" : feedback_ko.name}

        after = time.time()
        print(after - before)
        return render(request, 'pr.html', context)
    else:
        return HttpResponse("No projects found\n", status=404)
