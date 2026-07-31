from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),

    path('hospitals/', views.citizen_hospital_list, name='citizen_hospitals'),
    path('hospitals/<int:pk>/', views.citizen_hospital_detail, name='citizen_hospital_detail'),
    path('request-ambulance/', views.ambulance_request_create, name='request_ambulance'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('my-requests/<int:pk>/', views.request_detail, name='request_detail'),

    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/availability/', views.staff_update_availability, name='staff_update_availability'),
    path('staff/requests/', views.staff_incoming_requests, name='staff_requests'),
    path('staff/requests/<int:pk>/accept/', views.staff_accept_request, name='staff_accept_request'),
    path('staff/requests/<int:pk>/<str:action>/', views.staff_transition_request, name='staff_transition_request'),

    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/accounts/', views.admin_pending_accounts, name='admin_pending_accounts'),
    path('admin-panel/accounts/create-staff/', views.admin_create_staff_account, name='admin_create_staff_account'),
    path('admin-panel/accounts/<int:pk>/verify/', views.admin_verify_account, name='admin_verify_account'),
    path('admin-panel/accounts/<int:pk>/reject/', views.admin_reject_account, name='admin_reject_account'),
    path('admin-panel/accounts/<int:pk>/link/', views.admin_link_staff_to_hospital, name='admin_link_staff'),
    path('admin-panel/hospitals/', views.admin_hospital_list, name='admin_hospitals'),
    path('admin-panel/hospitals/<int:pk>/toggle/', views.admin_toggle_hospital_active, name='admin_toggle_hospital'),
]