import ujson
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
#
def slack_chat(request):
    data = ujson.loads(request.body)
    # import ipdb;ipdb.set_trace()
    print(data)
    return JsonResponse(data)
