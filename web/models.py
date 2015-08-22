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
from django.db import models
from gm_pr import settings


class SlackSettings(models.Model):
    """ Slack settings
    """

    slack_token = models.CharField(max_length=256)
    slack_url = models.CharField(max_length=256)


class LabelGithub(models.Model):
    """ List of label from github
    """

    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name


class GeneralSettings(models.Model):
    """ General settings like url and stuuf like that
    """

    weburl = models.CharField(max_length=256)
    github_oauth_token = models.CharField(max_length=256)
    organization = models.CharField(max_length=256)
    top_level_url = models.CharField(max_length=256, default=settings.TOP_LEVEL_URL)
    old_period = models.IntegerField(default=4, null=True, blank=True)
    slack_settings = models.ForeignKey(SlackSettings, null=True, blank=True)
    label_github = models.ManyToManyField(LabelGithub, null=True, default=None, blank=True)


    def __str__(self):
        return "%s -- %s" % (self.organization, self.weburl)


class ProjectRepository(models.Model):
    """ Project repository
    """

    general_settings = models.ManyToManyField(GeneralSettings, null=True, blank=True)
    parent = models.ForeignKey('self', null=True, default=None, blank=True)
    name = models.CharField(max_length=256)

    def __eq__(self, other):
        return self.name == other

    def __str__(self):
        return self.name
