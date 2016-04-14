from django.http import JsonResponse
from django.shortcuts import render
from usernames import is_safe_username
import json

# Create your views here.
def sign(request):
    response = {
        'status': 200,
        'response': 'god'
    }
    return JsonResponse(response)