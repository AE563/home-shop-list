from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    # Pages
    path('', views.view_page, name='view'),
    path('edit/', views.edit_page, name='edit'),
    # Purchase API
    path('api/purchases/', views.create_purchase, name='create-purchase'),
    path('api/purchases/<int:pk>/', views.purchase_detail, name='purchase-detail'),
    path('api/purchases/<int:pk>/toggle/', views.toggle_purchase, name='toggle-purchase'),
    # Category API
    path('api/categories/', views.create_category, name='create-category'),
    path('api/categories/<int:pk>/', views.category_detail, name='category-detail'),
]
