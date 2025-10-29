from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("<h5> хуй </h5>")
