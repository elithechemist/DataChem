from django.urls import path
from .views import PerformRegressionView, RegressionView, upload_file, project_response_table, update_values, download_project_pdf, ajax_get_project_data, add_column, remove_column

app_name = 'stats'

urlpatterns = [
    path('', project_response_table, name='home'),
    path('upload/', upload_file, name='upload'),
    path('project/<int:project_id>/response_table/', project_response_table, name='project_response_table'),
    path('project/<int:project_id>/update_values/', update_values, name='update_values'),
    path('project/<int:project_id>/pdf/', download_project_pdf, name='project_pdf'),
    path('ajax/project/<int:project_id>/data/', ajax_get_project_data, name='ajax_get_project_data'),
    path('add_column/<int:project_id>/', add_column, name='add_column'),
    path('remove_column/<int:project_id>/', remove_column, name='remove_column'),
    path('regression/', RegressionView.as_view(), name='regression_view'),
    path('perform_regression/', PerformRegressionView.as_view(), name='perform_regression'),
]