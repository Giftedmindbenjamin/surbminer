from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    
    # Deposit Management
    path('deposits/', views.deposit_management, name='deposit_management'),
    path('deposits/<int:deposit_id>/approve/', views.approve_deposit, name='approve_deposit'),
    path('deposits/<int:deposit_id>/cancel/', views.cancel_deposit, name='cancel_deposit'),
    
    # Withdrawal Management
    path('withdrawals/', views.withdrawal_management, name='withdrawal_management'),
    path('withdrawals/<int:withdrawal_id>/approve/', views.approve_withdrawal, name='approve_withdrawal'),
    path('withdrawals/<int:withdrawal_id>/cancel/', views.cancel_withdrawal, name='cancel_withdrawal'),
    
    # Investment Management
    path('investments/', views.investment_management, name='investment_management'),
    
    # Transactions & Reports
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('reports/', views.reports, name='reports'),
    
    # Admin Tools
    path('logs/', views.admin_logs, name='admin_logs'),
    path('notifications/', views.notifications, name='notifications'),
    path('settings/', views.site_settings, name='site_settings'),
]