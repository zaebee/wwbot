import os
import ujson
import logging

from django.http import JsonResponse
from django.shortcuts import render

from slackclient import SlackClient


SLACK_BOT_USER = 'wwdeploy'
SLACK_BOT_MENTION = '<@%s>' % SLACK_BOT_USER
SLACK_BOT_NAME = 'wwdeploy'
SLACK_CHANNEL = 'deploy'

SLACK_TOKEN = os.environ.get('SLACK_TOKEN')

slack_client = SlackClient(SLACK_TOKEN)


def slack_chat(request):
    data = ujson.loads(request.body)
    # import ipdb;ipdb.set_trace()
    print(data)
    return JsonResponse(data)
