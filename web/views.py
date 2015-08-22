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

from gm_pr import settings_projects
from common import proj_repo
from common.prfetcher import PrFetcher
from web.models import ProjectRepository, GeneralSettings


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

        prf = PrFetcher(general_settings.top_level_url, general_settings.organization, repos)
        context = {"title" : "%s PR list" % project,
                   "project_list" : prf.get_prs(),
                   "feedback_ok" : settings_projects.FEEDBACK_OK['name'],
                   "feedback_weak" : settings_projects.FEEDBACK_WEAK['name'],
                   "feedback_ko" : settings_projects.FEEDBACK_KO['name']}

        after = time.time()
        print(after - before)
        return render(request, 'pr.html', context)
    else:
        return HttpResponse("No projects found\n", status=404)
