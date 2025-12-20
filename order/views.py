from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from goods import models
from .models import Order, OrderFile
from .forms import OrderForm
from django.views.generic import ListView
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
@login_required
def create_order(request):
    """Функциональное представление для создания заказа"""
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            order = form.save()
            
            # Обработка файлов
            files = request.FILES.getlist('files')
            for file in files:
                OrderFile.objects.create(order=order, file=file)
            
            messages.success(request, 'Заказ успешно создан!')
            return redirect('order:detail', pk=order.pk)
    else:
        form = OrderForm(user=request.user)
    
    return render(request, 'order/order_form.html', {
        'form': form,
        'title': 'Создание нового заказа'
    })

class OrderCreateView(LoginRequiredMixin, CreateView):
    """Класс-базированное представление для создания заказа"""
    model = Order
    form_class = OrderForm
    template_name = 'order/order_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
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

        # Дополнительная отладочная информация
        context['user_orders_customer_count'] = Order.objects.filter(customer=self.request.user).count()
        context['user_orders_freelancer_count'] = Order.objects.filter(freelancer=self.request.user).count()

        # Добавляем информацию о роли пользователя в каждом заказе
        orders_with_role = []
        for order in context['orders']:
            order.user_role = 'customer' if order.customer == self.request.user else 'freelancer'
            orders_with_role.append(order)
        context['orders'] = orders_with_role

        return context
    
def get_queryset(self):
    queryset = super().get_queryset()
    
    queryset = queryset.filter(
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
    

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'order/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Для не-суперпользователей показываем только их заказы
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                Q(customer=self.request.user) |
                Q(freelancer=self.request.user)
            )
        return queryset
    
@login_required
@require_POST
def cancel_order(request, pk):
    """Отмена заказа (только для заказчика)"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверяем, что пользователь - заказчик
    if order.customer != request.user:
        messages.error(request, 'Вы не можете отменить этот заказ')
        return redirect('order:detail', pk=pk)
    
    # Проверяем, что заказ еще открыт
    if order.status != 'open':
        messages.error(request, 'Можно отменить только открытые заказы')
        return redirect('order:detail', pk=pk)
    
    # Меняем статус
    order.status = 'canceled'
    order.save()
    
    messages.success(request, 'Заказ успешно отменен')
    return redirect('order:detail', pk=pk)

@login_required
@require_POST
def complete_order(request, pk):
    """Завершение заказа (только для исполнителя)"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверяем, что пользователь - исполнитель
    if order.freelancer != request.user:
        messages.error(request, 'Вы не можете завершить этот заказ')
        return redirect('order:detail', pk=pk)
    
    # Проверяем, что заказ в работе
    if order.status != 'in_progress':
        messages.error(request, 'Можно завершить только заказы в работе')
        return redirect('order:detail', pk=pk)
    
    # Меняем статус
    order.status = 'completed'
    order.save()
    
    messages.success(request, 'Заказ успешно завершен')
    return redirect('order:detail', pk=pk)

@login_required
def apply_to_order(request, pk):
    """Отклик на заказ"""
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
        # Здесь логика обработки отклика
        message = request.POST.get('message', '')
        proposed_price = request.POST.get('proposed_price')
        
        # TODO: Создать модель для откликов
        # Application.objects.create(
        #     order=order,
        #     freelancer=request.user,
        #     message=message,
        #     proposed_price=proposed_price
        # )
        
        messages.success(request, 'Ваш отклик успешно отправлен')
        return redirect('order:detail', pk=pk)
    
    # Если GET-запрос, показываем форму
    return render(request, 'order/apply_form.html', {'order': order})