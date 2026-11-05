from django.urls import path
from . import views

app_name = 'career_interests'
urlpatterns = [
    path('', views.questionnaire, name='questionnaire'),
    path('suggestions/', views.suggestions, name='suggestions'),
    path('save/', views.save_interests, name='save'),
    path('saved/', views.questionnaire_saved, name='questionnaire_saved'),
]
