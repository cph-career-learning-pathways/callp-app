from django.shortcuts import render
from .models import CareerResource

# Create your views here.
def index(request):
    return render(request, "front_end/index.html", {"username": "AWS Student"})

def resource_query(request):
    resources = CareerResource.objects.all()[:50]
    return render(request, "front_end/resource_query.html", {"resources": resources})