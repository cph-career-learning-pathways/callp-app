import logging
from requests.exceptions import HTTPError

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse


def AboutUs(request):
    return render(request, 'about_us.html')

def ContactUs(request):
    return render(request, 'contact_us.html')

def Feedback(request):
    return render(request, 'feedback.html')

def LicensePage(request):
    return render(request, 'license_page.html')

def UserManual(request):
    return render(request, 'user_manual.html')

def GitHubPage(request):
    return redirect('https://github.com/cph-career-learning-pathways/callp-app')