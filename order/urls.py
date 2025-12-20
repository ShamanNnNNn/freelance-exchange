from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    path('create/', views.create_order, name='create'),
    path('list/', views.OrderListView.as_view(), name='list'),
    path('<int:pk>/', views.OrderDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.OrderUpdateView.as_view(), name='edit'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel'),
    path('<int:pk>/complete/', views.complete_order, name='complete'),
    path('<int:pk>/apply/', views.apply_to_order, name='apply'),
]