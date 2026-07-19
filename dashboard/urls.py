from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.staff_login, name='login'),
    path('logout/', views.staff_logout, name='logout'),
    path('', views.dashboard_home, name='home'),

    path('menu-items/', views.menu_item_list, name='menu_item_list'),
    path('menu-items/import/', views.menu_item_import, name='menu_item_import'),
    path('menu-items/add/', views.menu_item_create, name='menu_item_create'),
    path('menu-items/<int:pk>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('menu-items/<int:pk>/delete/', views.menu_item_delete, name='menu_item_delete'),

    path('site-text/', views.site_text_list, name='site_text_list'),
    path('site-text/add/', views.site_text_create, name='site_text_create'),
    path('site-text/<int:pk>/edit/', views.site_text_edit, name='site_text_edit'),
    path('site-text/<int:pk>/delete/', views.site_text_delete, name='site_text_delete'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.ingredient_create, name='ingredient_create'),
    path('inventory/<int:pk>/edit/', views.ingredient_edit, name='ingredient_edit'),
    path('inventory/<int:pk>/delete/', views.ingredient_delete, name='ingredient_delete'),
    path('inventory/<int:pk>/restock/', views.ingredient_restock, name='ingredient_restock'),

    path('sales/record/', views.record_sale, name='record_sale'),
    path('sales/history/', views.sales_history, name='sales_history'),
    path('sales/reports/', views.sales_reports, name='sales_reports'),
    path('sales/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/void/', views.sale_void, name='sale_void'),

    path('staff-accounts/', views.staff_user_list, name='staff_user_list'),
    path('staff-accounts/add/', views.staff_user_create, name='staff_user_create'),
    path('staff-accounts/<int:pk>/edit/', views.staff_user_edit, name='staff_user_edit'),
    path('staff-accounts/<int:pk>/password/', views.staff_user_set_password, name='staff_user_set_password'),
    path('staff-accounts/<int:pk>/delete/', views.staff_user_delete, name='staff_user_delete'),

    path('schedule/', views.schedule_list, name='schedule_list'),
    path('schedule/add/', views.schedule_create, name='schedule_create'),
    path('schedule/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedule/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),

    path('contact-messages/', views.contact_message_list, name='contact_message_list'),
    path('contact-messages/<int:pk>/', views.contact_message_detail, name='contact_message_detail'),
    path('contact-messages/<int:pk>/delete/', views.contact_message_delete, name='contact_message_delete'),

    path('venue-requests/', views.venue_request_list, name='venue_request_list'),
    path('venue-requests/<int:pk>/edit/', views.venue_request_edit, name='venue_request_edit'),
    path('venue-calendar/', views.venue_calendar, name='venue_calendar'),

    path('mail/', views.mailbox_inbox, name='mailbox_inbox'),
    path('mail/compose/', views.mailbox_compose, name='mailbox_compose'),
    path('mail/<str:uid>/', views.mailbox_message_detail, name='mailbox_message_detail'),
    path('mail/<str:uid>/reply/', views.mailbox_reply, name='mailbox_reply'),
    path('mail/<str:uid>/delete/', views.mailbox_delete, name='mailbox_delete'),
]
