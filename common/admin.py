from django.contrib import admin
from django.contrib.auth.models import Group, User
from djcelery.models import TaskState, WorkerState, IntervalSchedule, CrontabSchedule, PeriodicTask

admin.site.unregister(TaskState)
admin.site.unregister(WorkerState)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(PeriodicTask)
admin.site.unregister(Group)
admin.site.unregister(User)