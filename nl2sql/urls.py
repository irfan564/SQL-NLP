from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/generate-execute/', views.api_generate_and_execute, name='api_generate_and_execute'),
    path('api/dataset-browse/', views.api_dataset_browse, name='api_dataset_browse'),
    path('api/schema/', views.api_schema, name='api_schema'),
]
