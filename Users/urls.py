from django.urls import path
from . import views


urlpatterns = [
    path('', views.login_view, name='login'),                      
    path('logout/', views.logout_view, name='logout'),            
    path('redirect/', views.redirect_by_role, name='redirect_by_role'),  
    path('register/', views.register_view, name='register'),     
    
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints/new/', views.file_complaint, name='file_complaint'),
    path('admin/complaints/', views.admin_complaints, name='admin_complaints'),
    path('admin/complaints/respond/<int:complaint_id>/', views.respond_complaint, name='respond_complaint'),  
]
