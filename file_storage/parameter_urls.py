from django.urls import path
from .views import parameter_view

urlpatterns = [
    path('<str:parameter_name>/<int:project_id>/', parameter_view, name='parameter'),
]
