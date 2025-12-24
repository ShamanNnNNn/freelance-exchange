from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse

from .models import Order, OrderFile
from .forms import OrderForm


class AllOrdersListView(ListView):
    """ВСЕ заказы на бирже (главная страница)"""
    model = Order
    template_name = 'order/all_orders.html'
    context_object_name = 'orders'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Order.objects.all().select_related('customer', 'freelancer')
        
        # Фильтрация по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Фильтрация по категории
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Фильтр по участию пользователя
        participation = self.request.GET.get('participation')
        if participation == 'my_orders' and self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(customer=self.request.user) |
                Q(freelancer=self.request.user)
            )
        elif participation == 'customer' and self.request.user.is_authenticated:
            queryset = queryset.filter(customer=self.request.user)
        elif participation == 'freelancer' and self.request.user.is_authenticated:
            queryset = queryset.filter(freelancer=self.request.user)
        
        # Сортировка
        order_by = self.request.GET.get('order_by', '-created_at')
        if order_by == 'default':
            order_by = '-created_at'
        
        if order_by in ['budget', '-budget', 'deadline', '-deadline', 'created_at', '-created_at']:
            queryset = queryset.order_by(order_by)
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика для всех заказов
        context['all_count'] = Order.objects.count()
        context['open_count'] = Order.objects.filter(status='open').count()
        context['in_progress_count'] = Order.objects.filter(status='in_progress').count()
        context['completed_count'] = Order.objects.filter(status='completed').count()
        context['canceled_count'] = Order.objects.filter(status='canceled').count()
        
        # Добавляем информацию о роли пользователя в каждом заказе
        orders_with_info = []
        for order in context['orders']:
            if self.request.user.is_authenticated:
                if order.customer == self.request.user:
                    order.user_role = 'customer'
                    order.is_mine = True
                elif order.freelancer == self.request.user:
                    order.user_role = 'freelancer'
                    order.is_mine = True
                else:
                    order.user_role = 'none'
                    order.is_mine = False
            else:
                order.user_role = 'none'
                order.is_mine = False
            orders_with_info.append(order)
        
        context['orders'] = orders_with_info
        context['title'] = 'Фриланс-биржа | Все заказы'
        
        return context


class MyOrdersListView(LoginRequiredMixin, ListView):
    """ТОЛЬКО мои заказы (требует авторизации)"""
    model = Order
    template_name = 'order/my_orders.html'
    context_object_name = 'orders'
    paginate_by = 12
    
    def get_queryset(self):
        # Только заказы текущего пользователя
        queryset = Order.objects.filter(
            Q(customer=self.request.user) |
            Q(freelancer=self.request.user)
        ).select_related('customer', 'freelancer')
        
        # Фильтрация по роли
        role = self.request.GET.get('role')
        if role == 'customer':
            queryset = queryset.filter(customer=self.request.user)
        elif role == 'freelancer':
            queryset = queryset.filter(freelancer=self.request.user)
        
        # Фильтрация по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Фильтрация по категории
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика для текущего пользователя
        user_orders = Order.objects.filter(
            Q(customer=self.request.user) |
            Q(freelancer=self.request.user)
        )
        
        context['my_all_count'] = user_orders.count()
        context['my_open_count'] = user_orders.filter(status='open').count()
        context['my_in_progress_count'] = user_orders.filter(status='in_progress').count()
        context['my_completed_count'] = user_orders.filter(status='completed').count()
        context['my_canceled_count'] = user_orders.filter(status='canceled').count()
        context['title'] = 'Мои заказы'
        
        # Добавляем информацию о роли пользователя
        orders_with_role = []
        for order in context['orders']:
            order.user_role = 'customer' if order.customer == self.request.user else 'freelancer'
            orders_with_role.append(order)
        context['orders'] = orders_with_role
        
        return context


class OrderCreateView(LoginRequiredMixin, CreateView):
    """Создание нового заказа"""
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.customer = self.request.user
        response = super().form_valid(form)
        
        # Обработка файлов
        files = self.request.FILES.getlist('files')
        for file in files:
            OrderFile.objects.create(order=self.object, file=file)
        
        messages.success(self.request, 'Заказ успешно создан!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('order:detail', kwargs={'pk': self.object.pk})


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование заказа"""
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'
    
    def get_queryset(self):
        # Только заказчик может редактировать свой заказ
        return Order.objects.filter(customer=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Обработка новых файлов
        files = self.request.FILES.getlist('files')
        for file in files:
            OrderFile.objects.create(order=self.object, file=file)
        
        messages.success(self.request, 'Заказ успешно обновлен!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('order:detail', kwargs={'pk': self.object.pk})


class OrderDetailView(DetailView):
    """Детальная информация о заказе"""
    model = Order
    template_name = 'order/order_detail.html'
    context_object_name = 'order'

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'order/order_list.html'
    context_object_name = 'orders'
    paginate_by = 12
    
    def get_queryset(self):
        # ВСЕГДА показываем только заказы текущего пользователя
        # Даже если он суперпользователь
        queryset = Order.objects.filter(
            Q(customer=self.request.user) |
            Q(freelancer=self.request.user)
        )
        
        # Фильтрация по роли пользователя
        role = self.request.GET.get('role')
        if role == 'customer':
            queryset = queryset.filter(customer=self.request.user)
        elif role == 'freelancer':
            queryset = queryset.filter(freelancer=self.request.user)
        
        # Фильтрация по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Фильтрация по категории
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем заказы только для текущего пользователя для статистики
        user_orders = Order.objects.filter(
            Q(customer=self.request.user) |
            Q(freelancer=self.request.user)
        )
        
        # Статистика для текущего пользователя
        context['all_count'] = user_orders.count()
        context['open_count'] = user_orders.filter(status='open').count()
        context['in_progress_count'] = user_orders.filter(status='in_progress').count()
        context['completed_count'] = user_orders.filter(status='completed').count()
        context['canceled_count'] = user_orders.filter(status='canceled').count()
        
        # Добавляем информацию о роли пользователя в каждом заказе
        orders_with_role = []
        for order in context['orders']:
            order.user_role = 'customer' if order.customer == self.request.user else 'freelancer'
            orders_with_role.append(order)
        context['orders'] = orders_with_role
        
        return context

@login_required
def apply_to_order(request, pk):
    """Отклик на заказ"""
    try:
        order = get_object_or_404(Order, pk=pk)
        
        # Проверяем, что пользователь не заказчик
        if order.customer == request.user:
            messages.error(request, 'Вы не можете откликнуться на свой заказ')
            return redirect('order:detail', pk=pk)
        
        # Проверяем, что заказ открыт
        if order.status != 'open':
            messages.error(request, 'Нельзя откликнуться на закрытый заказ')
            return redirect('order:detail', pk=pk)
        
        if request.method == 'POST':
            # Обработка данных формы
            message = request.POST.get('message', '').strip()
            proposed_price = request.POST.get('proposed_price')
            proposed_deadline = request.POST.get('proposed_deadline')
            portfolio_links = request.POST.get('portfolio_links', '').strip()
            
            # Валидация
            if not message:
                messages.error(request, 'Пожалуйста, напишите сообщение заказчику')
                return render(request, 'order/apply_form.html', {
                    'order': order,
                    'today': timezone.now().date(),
                    'form_data': {
                        'message': message,
                        'proposed_price': proposed_price,
                        'proposed_deadline': proposed_deadline,
                        'portfolio_links': portfolio_links,
                    }
                })
            
            
            messages.success(request, 'Ваш отклик успешно отправлен заказчику!')
            return redirect('order:detail', pk=pk)
        
        # Если GET-запрос, показываем форму
        context = {
            'order': order,
            'today': timezone.now().date()
        }
        return render(request, 'order/apply_form.html', context)
        
    except Exception as e:
        # Логирование ошибки (можно добавить позже)
        # import logging
        # logger = logging.getLogger(__name__)
        # logger.error(f"Error in apply_to_order: {str(e)}")
        
        messages.error(request, f'Произошла ошибка: {str(e)}')
        return redirect('order:list')

@login_required
@require_POST
def cancel_order(request, pk):
    """Отмена заказа (только для заказчика)"""
    order = get_object_or_404(Order, pk=pk)
    
    if order.customer != request.user:
        messages.error(request, 'Вы не можете отменить этот заказ')
        return redirect('order:detail', pk=pk)
    
    if order.status != 'open':
        messages.error(request, 'Можно отменить только открытые заказы')
        return redirect('order:detail', pk=pk)
    
    order.status = 'canceled'
    order.save()
    
    messages.success(request, 'Заказ успешно отменен')
    return redirect('order:detail', pk=pk)


@login_required
@require_POST
def complete_order(request, pk):
    """Завершение заказа (только для исполнителя)"""
    order = get_object_or_404(Order, pk=pk)
    
    if order.freelancer != request.user:
        messages.error(request, 'Вы не можете завершить этот заказ')
        return redirect('order:detail', pk=pk)
    
    if order.status != 'in_progress':
        messages.error(request, 'Можно завершить только заказы в работе')
        return redirect('order:detail', pk=pk)
    
    order.status = 'completed'
    order.save()
    
    messages.success(request, 'Заказ успешно завершен')
    return redirect('order:detail', pk=pk)