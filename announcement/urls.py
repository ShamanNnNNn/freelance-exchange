from django.urls import path
from . import views

app_name = 'announcement'


urlpatterns = [
    path('create/', views.create_announcement, name='create'),
    path('my/', views.my_announcements, name='my_announcements'),  # Проверьте имя
    path('<int:pk>/', views.announcement_detail, name='detail'),
    path('<int:pk>/edit/', views.edit_announcement, name='edit'),
    path('<int:pk>/delete/', views.delete_announcement, name='delete'),
    path('<int:pk>/toggle/', views.toggle_announcement_status, name='toggle_status'),
    path('all/', views.all_announcements, name='all_announcements'),
]