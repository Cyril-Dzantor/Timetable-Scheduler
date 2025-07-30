from django.urls import path
from . import views


urlpatterns = [
    path('', views.login_view, name='login'),                      
    path('logout/', views.logout_view, name='logout'),            
    path('redirect/', views.redirect_by_role, name='redirect_by_role'),  
    path('register/', views.register_view, name='register'),     
    
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints_detail/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('complaints/new/', views.file_complaint, name='file_complaint'),
    path('complaints_admin/', views.admin_complaints, name='admin_complaints'),
    path('complaints_admin/respond/<int:complaint_id>/', views.respond_complaint, name='respond_complaint'),  
]
