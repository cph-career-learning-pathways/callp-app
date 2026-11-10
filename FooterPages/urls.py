# Urls for footer pages.
from django.urls import path

from .views import AboutUs, ContactUs, Feedback, HumboldtPage, LicensePage, UserManual, GitHubPage


urlpatterns = [
    path("about-us/", AboutUs, name="about-us"),
    path("contact-us/", ContactUs, name="contact-us"),
    path("feedback/", Feedback, name="feedback"),
    path("license/", LicensePage, name="license-page"),
    path("user-manual/", UserManual, name="user-manual"),
    path("github/", GitHubPage, name="github-page"),
    path("humboldt/", HumboldtPage, name="humboldt-page"),
]