from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.staff_login, name='login'),
    path('logout/', views.staff_logout, name='logout'),
    path('', views.dashboard_home, name='home'),

    path('menu-items/', views.menu_item_list, name='menu_item_list'),
    path('menu-items/add/', views.menu_item_create, name='menu_item_create'),
    path('menu-items/<int:pk>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('menu-items/<int:pk>/delete/', views.menu_item_delete, name='menu_item_delete'),

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

    path('schedule/', views.schedule_list, name='schedule_list'),
    path('schedule/add/', views.schedule_create, name='schedule_create'),
    path('schedule/<int:pk>/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedule/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
]
