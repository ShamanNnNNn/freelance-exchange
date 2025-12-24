from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    # Главная страница - ВСЕ заказы на бирже
    path('', views.AllOrdersListView.as_view(), name='all_orders'),
    
    # Мои заказы (требует авторизации)
    path('my/', views.MyOrdersListView.as_view(), name='my_orders'),
    
    # Детальный просмотр заказа
    path('<int:pk>/', views.OrderDetailView.as_view(), name='detail'),
    
    # Создание заказа
    path('create/', views.OrderCreateView.as_view(), name='create'),
    
    path('list/', views.OrderListView.as_view(), name='list'),
    
    # Редактирование заказа
    path('<int:pk>/edit/', views.OrderUpdateView.as_view(), name='edit'),
    
    # Отклик на заказ
    path('<int:pk>/apply/', views.apply_to_order, name='apply'),
    
    # Действия с заказом
    path('<int:pk>/cancel/', views.cancel_order, name='cancel'),
    path('<int:pk>/complete/', views.complete_order, name='complete'),
]