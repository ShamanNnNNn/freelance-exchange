from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
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
    path('<int:pk>/complete/', views.complete_order, name='complete'),
    
    # Действия с откликами
    path('<int:pk>/applications/<int:application_pk>/accept/', views.accept_application, name='accept_application'),
    path('<int:pk>/applications/<int:application_pk>/reject/', views.reject_application, name='reject_application'),
    path('<int:pk>/applications/<int:application_pk>/withdraw/', views.withdraw_application, name='withdraw_application'),
    
    # Отмена заказа
    path('<int:pk>/cancel/', views.cancel_order, name='cancel'),
    path('<int:pk>/cancel/request/', views.request_cancellation, name='request_cancellation'),
    path('<int:pk>/cancel/confirm/', views.confirm_cancellation, name='confirm_cancellation'),
    path('<int:pk>/cancel/reject/', views.reject_cancellation, name='reject_cancellation'),
    path('<int:pk>/cancel/revoke/', views.revoke_cancellation, name='revoke_cancellation'),
    
    path('<int:pk>/delete/', views.delete_order, name='delete'),
]