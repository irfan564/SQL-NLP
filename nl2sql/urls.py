from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/nl2sql/', views.api_nl2sql, name='api_nl2sql'),
    path('api/run-sql/', views.api_run_sql, name='api_run_sql'),
    path('api/generate-execute/', views.api_generate_and_execute, name='api_generate_and_execute'),
    path('api/dataset-browse/', views.api_dataset_browse, name='api_dataset_browse'),
    path('api/schema/', views.api_schema, name='api_schema'),
]
