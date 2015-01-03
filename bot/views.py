from django.http import HttpResponse

from bot import tasks, slackAuth

@slackAuth.isFromSlack
def index(request):
    tasks.slack.delay()
    return HttpResponse("One moment, Octocat is considering your request\n")
