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
from django.db.utils import OperationalError

class GithubTokenHttpsHandler(request.HTTPSHandler):
    def __init__(self, token, **kwargs):
        super().__init__(**kwargs)
        self.__token = token

    def https_request(self, req):
        super().https_request(req)
        req.add_header('Authorization', 'token %s' % self.__token)

        return req

try:
    general_settings = GeneralSettings.objects.first()
    # if general_settings is None, this means we have migrated the DB
    # but have not yet gone into the admin page to enter data
    if general_settings is not None:
        handler = GithubTokenHttpsHandler(general_settings.github_oauth_token)
        opener = request.build_opener(handler)
        request.install_opener(opener)
except OperationalError:
    # We get here when migrating the DB: the GeneralSettings object doesn't exist
    # at all, so we can't get the OAuth token for the requests
    # (We don't need this during migration anyway)
    pass

