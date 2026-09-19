from django.urls import path
from . import views, api_views

urlpatterns = [
    # Public & Tracking
    path('', views.home_view, name='home'),
    path('track/', views.track_complaint_view, name='track_complaint'),

    # Authentication & Role Redirection
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('login-redirect/', views.login_redirect_view, name='login_redirect'),
    path('logout/', views.logout_view, name='logout'),

    # Consumer Portal
    path('dashboard/', views.consumer_dashboard_view, name='consumer_dashboard'),
    path('complaints/new/', views.complaint_create_view, name='complaint_create'),
    path('complaints/<str:complaint_id>/', views.complaint_detail_view, name='complaint_detail'),

    # Authority / Admin Portal
    path('admin-portal/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-portal/review/<str:complaint_id>/', views.admin_review_complaint_view, name='admin_review_complaint'),
    path('admin-portal/export/csv/', views.admin_export_csv_view, name='admin_export_csv'),

    # REST APIs & AI Modules
    path('api/complaints/', api_views.ComplaintListCreateAPIView.as_view(), name='api_complaint_list_create'),
    path('api/complaints/<int:pk>/', api_views.ComplaintDetailAPIView.as_view(), name='api_complaint_detail'),
    path('api/complaints/<str:complaint_id>/duplicates/', api_views.ComplaintDuplicatesAPIView.as_view(), name='api_complaint_duplicates'),
    path('api/track/<str:complaint_id>/', api_views.ComplaintTrackPublicAPIView.as_view(), name='api_complaint_track'),
    path('api/stats/', api_views.GrievanceStatsAPIView.as_view(), name='api_grievance_stats'),
    path('api/assistant/', api_views.AIAssistantAPIView.as_view(), name='api_assistant'),
]
