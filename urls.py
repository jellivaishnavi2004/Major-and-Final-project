from django.urls import path
from django.views.generic import TemplateView
from .views import * 

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('user_dashboard/', user_dashboard, name='user_dashboard'),
    path('upload_file/,', upload_file, name='upload_file'),
    path('logout/', logout, name='logout'),
    path('upload/', upload_file, name='upload_file'),
    path('api/files/', get_uploaded_files, name='get_uploaded_files'),
    path('files/', file_list, name='file_list'),
    path('files/download/<uuid:file_id>/', download_file, name='download_file'),
    path('files/delete/<uuid:file_id>/', delete_file, name='delete_file'),
]