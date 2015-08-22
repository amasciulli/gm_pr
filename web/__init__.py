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



from urllib import request
from web.models import GeneralSettings

class GithubTokenHttpsHandler(request.HTTPSHandler):
    def __init__(self, token, **kwargs):
        super().__init__(**kwargs)
        self.__token = token

    def https_request(self, req):
        super().https_request(req)
        req.add_header('Authorization', 'token %s' % self.__token)

        return req

#FIXME initital migration
general_settings = GeneralSettings.objects.first()
handler = GithubTokenHttpsHandler(general_settings.github_oauth_token)
opener = request.build_opener(handler)

request.install_opener(opener)
