from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render

def main_v(request: HttpRequest):
    return HttpResponse("Salom !")