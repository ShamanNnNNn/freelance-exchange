from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.db.models import Q
from .models import Order

def all_orders(request):
    page = request.GET.get('page', 1)
    status = request.GET.get('status', None)
    category = request.GET.get('category', None)
    participation = request.GET.get('participation', None)
    order_by = request.GET.get('order_by', '-created_at')
    
    # Базовый queryset - ВСЕ заказы для глобальной статистики
    all_orders_queryset = Order.objects.all()
    
    # queryset для фильтрации - начинаем с всех заказов
    filtered_orders = Order.objects.all()
    
    # Фильтрация по статусу
    if status and status != 'all':
        filtered_orders = filtered_orders.filter(status=status)
    
    # Фильтрация по категории
    if category and category != 'all':
        filtered_orders = filtered_orders.filter(category=category)
    
    # Фильтрация по участию пользователя
    if participation:
        if participation == 'my_orders':
            filtered_orders = filtered_orders.filter(Q(customer=request.user) | Q(freelancer=request.user))
        elif participation == 'customer':
            filtered_orders = filtered_orders.filter(customer=request.user)
        elif participation == 'freelancer':
            filtered_orders = filtered_orders.filter(freelancer=request.user)
    
    # Сортировка
    if order_by and order_by != 'default':
        if order_by in ['created_at', '-created_at', 'deadline', '-deadline', 
                        'budget', '-budget', 'updated_at', '-updated_at']:
            filtered_orders = filtered_orders.order_by(order_by)
    else:
        filtered_orders = filtered_orders.order_by('-created_at')
    
    # Пагинация ТОЛЬКО для отфильтрованных заказов
    paginator = Paginator(filtered_orders, 12)
    
    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        current_page = paginator.page(1)
    except EmptyPage:
        current_page = paginator.page(paginator.num_pages)
    
    # ГЛОБАЛЬНАЯ статистика (все заказы на бирже)
    global_stats = {
        'all_count': all_orders_queryset.count(),
        'open_count': all_orders_queryset.filter(status='open').count(),
        'in_progress_count': all_orders_queryset.filter(status='in_progress').count(),
        'completed_count': all_orders_queryset.filter(status='completed').count(),
    }
    
    # ФИЛЬТРОВАННАЯ статистика (после применения фильтров)
    filtered_stats = {
        'filtered_count': filtered_orders.count(),
        'open_count_filtered': filtered_orders.filter(status='open').count(),
        'in_progress_count_filtered': filtered_orders.filter(status='in_progress').count(),
        'completed_count_filtered': filtered_orders.filter(status='completed').count(),
    }
    
    # Определяем, какие статистические данные показывать
    show_filtered_stats = any([
        status, category, participation, 
        order_by and order_by != '-created_at'
    ])
    
    context = {
        'orders': current_page,
        # Глобальная статистика (всегда)
        **global_stats,
        # Отфильтрованная статистика (всегда)
        **filtered_stats,
        # Флаг для отображения
        'show_filtered_stats': show_filtered_stats,
        # Параметры фильтрации для сохранения в форме
        'current_status': status or '',
        'current_category': category or '',
        'current_participation': participation or '',
        'current_order_by': order_by or '-created_at',
    }
    
    return render(request, 'order/all_orders.html', context)