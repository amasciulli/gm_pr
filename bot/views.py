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

from django.http import HttpResponse

from common import proj_repo
from bot import tasks, slackauth
from web.models import GeneralSettings


@slackauth.isFromSlack
def index(request):
    project, repos = proj_repo.proj_repo(request)
    general_settings = GeneralSettings.objects.first()

    if not general_settings:
        return HttpResponse("No configuration found\n", status=404)

    if repos:
        tasks.slack(general_settings.top_level_url,
                    general_settings.organization,
                    "%s?project=%s" % (general_settings.web_url, project),
                    repos,
                    general_settings.slack_settings.slack_url,
                    "#%s" % project)
        return HttpResponse("Octocat thank you for your business\n")
    else:
        return HttpResponse("No projects found\n", status=404)
