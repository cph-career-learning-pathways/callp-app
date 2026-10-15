from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, "front_end/index.html", {"username": "AWS Student"})

def resource_query(request):
    resources = [
        {"name": "EC2", "description": "Cloud compute instance"},
        {"name": "S3", "description": "Object storage service"},
        {"name": "RDS", "description": "Managed relational database"},
    ]
    return render(request, "resource_query.html", {"resources": resources})    