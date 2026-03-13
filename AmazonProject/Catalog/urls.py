from django.urls import path
from . import views

urlpatterns = [
    # --- Main ---
    path('', views.home, name='home'),

    # --- Staff Section ---
    path('staff-login/', views.staff_login, name='staff_login'),
    path('staff-logout/', views.staff_logout, name='staff_logout'),
    path('staffs/', views.staffs, name='staffs'), 
    
    # Staff - User Management
    path('add-user/', views.add_user, name='add_user'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('adjust-balance/<int:user_id>/', views.adjust_balance, name='adjust_balance'),
    path('reset-orders/<int:user_id>/', views.reset_user_orders, name='reset_user_orders'),
    path('staff/assign/<int:user_id>/', views.manual_assign_order, name='manual_assign_order'),
    
    # Staff - Order Template Management
    path('staff/order/add/', views.add_order_staff, name='add_order_staff'),
    path('staff/order/edit/<int:order_id>/', views.edit_order_staff, name='edit_order_staff'),
    path('staff/order/delete/<int:order_id>/', views.delete_order_staff, name='delete_order_staff'),

    # --- User Portal Section ---
    path('user-login/', views.user_login, name='user_login'), 
    path('user-register/', views.user_register, name='user_register'),
    path('user-logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    
    # FIXED: Both of these now point to user_record in views.py
    path('history/', views.user_wallet, name='user_wallet'),
    path('record/', views.user_record, name='user_record'),
    
    path('order/', views.user_order, name='user_order'),
    path('order/start/', views.start_matching, name='start_matching'),
    path('order/complete/<int:order_id>/', views.complete_order, name='complete_order'),
    path('settings/', views.user_settings, name='user_settings'),
]