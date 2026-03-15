from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # PUBLIC / CORE
    # ==========================================
    path('', views.home, name='home'),

    # ==========================================
    # STAFF PANEL (Administrative)
    # ==========================================
    path('staff/login/', views.staff_login, name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    path('staff/dashboard/', views.staffs, name='staffs'), 
    path('staff/users/add/', views.add_user, name='add_user'),
    path('staff/users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('staff/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('staff/users/adjust-balance/', views.adjust_balance, name='adjust_balance'),
    path('staff/users/reset-progress/<int:user_id>/', views.reset_user_orders, name='reset_user_orders'),
    path('staff/users/assign-task/<int:user_id>/', views.manual_assign_order, name='manual_assign_order'),
    path('staff/templates/add/', views.add_order_staff, name='add_order_staff'),
    path('staff/templates/edit/<int:order_id>/', views.edit_order_staff, name='edit_order_staff'),
    path('staff/templates/delete/<int:order_id>/', views.delete_order_staff, name='delete_order_staff'),
    path('staff/order-log/delete/<int:order_id>/', views.delete_order_record, name='delete_order_record'),
    path('staff/withdrawal/approve/<int:order_id>/', views.approve_withdrawal, name='approve_withdrawal'),
    path('staff/withdrawal/reject/<int:order_id>/', views.reject_withdrawal, name='reject_withdrawal'),

    # ==========================================
    # USER PORTAL (Member Area)
    # ==========================================
    path('user/login/', views.user_login, name='user_login'), 
    path('user/register/', views.user_register, name='user_register'),
    path('user/logout/', views.user_logout, name='user_logout'),
    
    # Dashboard & Profile
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('settings/', views.user_settings, name='user_settings'),
    
    # Security (Handles Login Password and Withdrawal PIN)
    path('settings/security/', views.security_settings, name='security_settings'),
    
    # Wallet Management
    path('wallet/edit/', views.edit_wallet, name='edit_wallet'),
    path('wallet/update-address/', views.update_wallet_address, name='update_wallet_address'),
    
    # Tasks / Orders
    path('order/', views.user_order, name='user_order'),
    path('order/start-match/', views.start_matching, name='start_matching'),
    path('order/submit/<int:order_id>/', views.complete_order, name='complete_order'),
    
    # Finance & Records
    path('wallet/', views.user_wallet, name='user_wallet'),
    path('withdraw/', views.withdraw_funds, name='withdraw_funds'),
    path('records/', views.user_record, name='user_record'),
]

# This connects the 404 view from your views.py
handler404 = 'Catalog.views.error_404_view'