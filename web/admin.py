from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from web.models import GeneralSettings, SlackSettings, ProjectRepository, LabelGithub


@admin.register(GeneralSettings)
class GeneralSettingsAdmin(ModelAdmin):
    pass


@admin.register(SlackSettings)
class SlackSettingsAdmin(ModelAdmin):
    pass


@admin.register(ProjectRepository)
class ProjectRepositoryAdmin(ModelAdmin):
    pass


@admin.register(LabelGithub)
class LabelGithubAdmin(ModelAdmin):
    pass
