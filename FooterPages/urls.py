# Urls for footer pages.
from django.urls import path

from .views import AboutUs, ContactUs, Feedback, LicensePage, UserManual, GitHubPage


urlpatterns = [
    path("about-us/", AboutUs, name="about-us"),
    path("contact-us/", ContactUs, name="contact-us"),
    path("license/", LicensePage, name="license"),
    path("user-manual/", UserManual, name="user-manual"),
    path("github/", GitHubPage, name="github"),
]