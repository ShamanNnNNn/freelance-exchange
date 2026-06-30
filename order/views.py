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
from .models import Order, CancellationRequest
from .models import Order, Application, Notification, OrderFile
from .forms import OrderForm, ApplicationForm
from .models import Order, Application, Notification, CancellationRequest, Category, Technology
from .models import Language
class AllOrdersListView(ListView):
    """ВСЕ заказы на бирже (главная страница)"""
    model = Order
    template_name = 'order/all_orders.html'
    context_object_name = 'orders'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Order.objects.filter(status='open').select_related('customer', 'freelancer')
        
        # ===== ПОИСК =====
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            # Разделяем поисковый запрос на слова
            search_words = search_query.split()
            
            # Создаем Q-объект для поиска
            q_objects = Q()
            
            for word in search_words:
                if word:
                    # Ищем по всем полям (без учета регистра)
                    q_objects |= (
                        Q(title__icontains=word) |
                        Q(description__icontains=word) |
                        Q(tags__icontains=word) |
                        Q(customer__username__icontains=word) |
                        Q(customer__first_name__icontains=word) |
                        Q(customer__last_name__icontains=word)
                    )
            
            queryset = queryset.filter(q_objects).distinct()
        
        # Фильтрация по статусу
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Фильтрация по категории
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Фильтрация по технологиям
        tech = self.request.GET.getlist('tech')
        if tech:
            queryset = queryset.filter(technologies__slug__in=tech).distinct()
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
        context['technologies'] = Technology.objects.all()
        context['categories'] = Category.objects.all()
        context['languages'] = Language.objects.prefetch_related('technology_set').all()
        # Получаем поисковый запрос
        search_query = self.request.GET.get('search', '').strip()
        context['search_query'] = search_query
        
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
        queryset = Order.objects.filter(
            Q(customer=self.request.user) |
            Q(freelancer=self.request.user)
        ).exclude(status='canceled').select_related('customer', 'freelancer')

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
            queryset = queryset.filter(category_id=category)

        # Фильтрация по технологиям
        tech = self.request.GET.getlist('tech')
        if tech:
            queryset = queryset.filter(technologies__slug__in=tech).distinct()

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['technologies'] = Technology.objects.all()
        context['categories'] = Category.objects.all()
        context['languages'] = Language.objects.prefetch_related('technology_set').all()
        context['selected_tech'] = self.request.GET.getlist('tech')

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = Language.objects.prefetch_related('technology_set').all()
        return context
    
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
    """Детальная информация о заказе с откликами"""
    model = Order
    template_name = 'order/order_detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем отклики в контекст
        context['applications'] = self.object.applications.select_related('freelancer').all()
        
        # Проверяем, откликался ли текущий пользователь
        if self.request.user.is_authenticated and self.request.user != self.object.customer:
            context['user_application'] = self.object.applications.filter(
                freelancer=self.request.user
            ).first()
        
        return context
    
    def get_object(self, queryset=None):
        """Получаем объект и увеличиваем счетчик просмотров"""
        obj = super().get_object(queryset)
        obj.increment_views()
        return obj


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'order/order_list.html'
    context_object_name = 'orders'
    paginate_by = 12
    
    def get_queryset(self):
        # ВСЕГДА показываем только заказы текущего пользователя
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


# ========== ОТДЕЛЬНЫЕ ФУНКЦИИ (НЕ МЕТОДЫ КЛАССА) ==========

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
    
    # Проверяем, не откликался ли уже
    if Application.objects.filter(order=order, freelancer=request.user).exists():
        messages.warning(request, 'Вы уже откликались на этот заказ')
        return redirect('order:detail', pk=pk)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.order = order
            application.freelancer = request.user
            application.save()
            
            # Увеличиваем счетчик откликов заказа
            order.increment_applications()
            
            # Создаем уведомление для заказчика
            Notification.objects.create(
                user=order.customer,
                title='Новый отклик на ваш заказ!',
                message=f'{request.user.get_full_name() or request.user.username} откликнулся на ваш заказ "{order.title}".',
                notification_type='application_received',
                related_object=f'order:{order.id}',
                is_important=True
            )
            
            messages.success(request, 'Ваш отклик успешно отправлен! Заказчик получил уведомление.')
            return redirect('order:detail', pk=pk)
    else:
        form = ApplicationForm(initial={'proposed_price': order.budget})
    
    return render(request, 'order/apply_form.html', {
        'form': form,
        'order': order
    })


@login_required
@require_POST
def accept_application(request, pk, application_pk):  # Измените application_id на application_pk
    """Принять отклик (только для заказчика)"""
    order = get_object_or_404(Order, pk=pk)
    application = get_object_or_404(Application, pk=application_pk, order=order)  # И здесь тоже
    
    # Проверяем, что пользователь - заказчик
    if order.customer != request.user:
        messages.error(request, 'Вы не можете принять этот отклик')
        return redirect('order:detail', pk=pk)
    
    # Проверяем, что заказ еще открыт
    if order.status != 'open':
        messages.error(request, 'Заказ уже не открыт')
        return redirect('order:detail', pk=pk)
    
    if application.accept():
        messages.success(request, f'Вы приняли отклик от {application.freelancer.username}. Заказ переведен в работу.')
    else:
        messages.error(request, 'Не удалось принять отклик')
    
    return redirect('order:detail', pk=pk)


@login_required
@require_POST
def reject_application(request, pk, application_pk):  # Измените application_id на application_pk
    """Отклонить отклик (только для заказчика)"""
    order = get_object_or_404(Order, pk=pk)
    application = get_object_or_404(Application, pk=application_pk, order=order)  # И здесь тоже
    
    if order.customer != request.user:
        messages.error(request, 'Вы не можете отклонить этот отклик')
        return redirect('order:detail', pk=pk)
    
    if application.reject():
        messages.success(request, 'Отклик отклонен')
    else:
        messages.error(request, 'Не удалось отклонить отклик')
    
    return redirect('order:detail', pk=pk)


@login_required
@require_POST
def withdraw_application(request, pk, application_pk):  # Измените application_id на application_pk
    """Отозвать свой отклик (только для исполнителя)"""
    order = get_object_or_404(Order, pk=pk)
    application = get_object_or_404(Application, pk=application_pk, order=order)  # И здесь тоже
    
    if application.freelancer != request.user:
        messages.error(request, 'Вы не можете отозвать этот отклик')
        return redirect('order:detail', pk=pk)
    
    if application.withdraw():
        messages.success(request, 'Вы отозвали свой отклик')
    else:
        messages.error(request, 'Не удалось отозвать отклик')
    
    return redirect('order:detail', pk=pk)

@login_required
@require_POST
def delete_order(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    
    if order.status not in ['open', 'canceled']:
        messages.error(request, 'Нельзя удалить заказ в текущем статусе.')
        return redirect('order:detail', pk=pk)
    
    order.delete()
    messages.success(request, 'Заказ удалён.')
    return redirect('order:my_orders')

@login_required
@require_POST
def cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk)

    # Проверка прав
    if order.customer != request.user:
        messages.error(request, 'У вас нет прав для отмены этого заказа.')
        return redirect('order:detail', pk=pk)

    if order.status != 'open':
        messages.error(request, 'Невозможно отменить заказ в текущем статусе.')
        return redirect('order:detail', pk=pk)

    # Получаем причину отмены
    reason = request.POST.get('cancel_reason', '')

    # Отменяем заказ
    order.status = 'canceled'
    order.save()

    # Логируем отмену
    # Можно создать запись в логе или историю изменений

    messages.success(request, 'Заказ успешно отменен.')
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



@login_required
@require_POST
def request_cancellation(request, pk):
    """Запрос на отмену заказа в работе"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверка прав
    if order.customer != request.user:
        messages.error(request, 'У вас нет прав для отмены этого заказа.')
        return redirect('order:detail', pk=pk)
    
    if order.status != 'in_progress':
        messages.error(request, 'Невозможно отменить заказ в текущем статусе.')
        return redirect('order:detail', pk=pk)
    
    # Проверяем, нет ли уже активного запроса
    if hasattr(order, 'cancellation_request'):
        if order.cancellation_request.status == 'pending':
            messages.warning(request, 'Запрос на отмену уже отправлен и ожидает подтверждения.')
            return redirect('order:detail', pk=pk)
    
    # Получаем причину отмены
    reason = request.POST.get('cancel_reason', '')
    
    # Создаем запрос на отмену
    cancellation_request = CancellationRequest.objects.create(
        order=order,
        customer=order.customer,
        freelancer=order.freelancer,
        reason=reason,
        status='pending'
    )
    
    # Меняем статус заказа
    order.status = 'cancelling'
    order.save()
    
    # Отправляем уведомление исполнителю
    # Здесь можно добавить отправку email или уведомление в системе
    
    messages.success(request, 'Запрос на отмену отправлен исполнителю. Заказ будет отменен после его подтверждения.')
    return redirect('order:detail', pk=pk)

@login_required
@require_POST
def confirm_cancellation(request, pk):
    """Исполнитель подтверждает отмену"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверка прав
    if order.freelancer != request.user:
        messages.error(request, 'У вас нет прав для этого действия.')
        return redirect('order:detail', pk=pk)
    
    if order.status != 'cancelling':
        messages.error(request, 'Нет активного запроса на отмену.')
        return redirect('order:detail', pk=pk)
    
    if not hasattr(order, 'cancellation_request'):
        messages.error(request, 'Запрос на отмену не найден.')
        return redirect('order:detail', pk=pk)
    
    cancellation_request = order.cancellation_request
    
    if cancellation_request.status != 'pending':
        messages.error(request, 'Запрос на отмену уже обработан.')
        return redirect('order:detail', pk=pk)
    
    # Подтверждаем отмену
    cancellation_request.status = 'confirmed'
    cancellation_request.responded_at = timezone.now()
    cancellation_request.save()
    
    # Отменяем заказ
    order.status = 'cancelled'
    order.save()
    
    # Отправляем уведомление заказчику
    messages.success(request, 'Вы подтвердили отмену заказа.')
    return redirect('order:detail', pk=pk)

@login_required
@require_POST
def reject_cancellation(request, pk):
    """Исполнитель отклоняет отмену"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверка прав
    if order.freelancer != request.user:
        messages.error(request, 'У вас нет прав для этого действия.')
        return redirect('order:detail', pk=pk)
    
    if order.status != 'cancelling':
        messages.error(request, 'Нет активного запроса на отмену.')
        return redirect('order:detail', pk=pk)
    
    if not hasattr(order, 'cancellation_request'):
        messages.error(request, 'Запрос на отмену не найден.')
        return redirect('order:detail', pk=pk)
    
    cancellation_request = order.cancellation_request
    
    if cancellation_request.status != 'pending':
        messages.error(request, 'Запрос на отмену уже обработан.')
        return redirect('order:detail', pk=pk)
    
    # Отклоняем отмену
    cancellation_request.status = 'rejected'
    cancellation_request.responded_at = timezone.now()
    cancellation_request.save()
    
    # Возвращаем заказ в работу
    order.status = 'in_progress'
    order.save()
    
    messages.success(request, 'Вы отклонили запрос на отмену.')
    return redirect('order:detail', pk=pk)

@login_required
@require_POST
def revoke_cancellation(request, pk):
    """Заказчик отзывает запрос на отмену"""
    order = get_object_or_404(Order, pk=pk)
    
    # Проверка прав
    if order.customer != request.user:
        messages.error(request, 'У вас нет прав для этого действия.')
        return redirect('order:detail', pk=pk)
    
    if order.status != 'cancelling':
        messages.error(request, 'Нет активного запроса на отмену.')
        return redirect('order:detail', pk=pk)
    
    if not hasattr(order, 'cancellation_request'):
        messages.error(request, 'Запрос на отмену не найден.')
        return redirect('order:detail', pk=pk)
    
    cancellation_request = order.cancellation_request
    
    if cancellation_request.status != 'pending':
        messages.error(request, 'Запрос на отмену уже обработан.')
        return redirect('order:detail', pk=pk)
    
    # Отзываем запрос
    cancellation_request.status = 'revoked'
    cancellation_request.responded_at = timezone.now()
    cancellation_request.save()
    
    # Возвращаем заказ в работу
    order.status = 'in_progress'
    order.save()
    
    messages.success(request, 'Запрос на отмену отозван.')
    return redirect('order:detail', pk=pk)

