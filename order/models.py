# order/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.paginator import Paginator

User = get_user_model()


class Order(models.Model):
    """Заказ на фриланс-бирже"""
    
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
        ('closed', 'Закрыт'),
        ('cancelling', 'В процессе отмены'),
    ]
    
    CATEGORY_CHOICES = [
        ('web', 'Веб-разработка'),
        ('mobile', 'Мобильная разработка'),
        ('design', 'Дизайн'),
        ('marketing', 'Маркетинг'),
        ('writing', 'Копирайтинг'),
        ('translation', 'Переводы'),
        ('other', 'Другое'),
    ]
    
    # Основные поля
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='open')
    category = models.CharField('Категория', max_length=50, choices=CATEGORY_CHOICES)
    budget = models.DecimalField('Бюджет', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField('Валюта', max_length=3, choices=[('RUB', '₽'), ('USD', '$'), ('EUR', '€')], default='RUB')
    deadline = models.DateField('Срок выполнения')
    tags = models.TextField('Теги', blank=True, help_text='Через запятую')
    
    # Пользователи
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                related_name='orders_as_customer', verbose_name='Заказчик')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                  related_name='orders_as_freelancer', verbose_name='Исполнитель',
                                  null=True, blank=True)
    
    # Даты
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    # Статистика
    views_count = models.PositiveIntegerField('Просмотры', default=0)
    applications_count = models.PositiveIntegerField('Отклики', default=0)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def increment_views(self):
        """Увеличить счетчик просмотров"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_applications(self):
        """Увеличить счетчик откликов"""
        self.applications_count += 1
        self.save(update_fields=['applications_count'])

    def can_be_cancelled_by(self, user):
            if self.status not in ['open', 'in_progress']:
                return False
            
            if user == self.customer:
                return True
            
            if user == self.freelancer and self.status == 'in_progress':
                return True
                
            return False
    
        
class Application(models.Model):
    """Отклик на заказ"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает рассмотрения'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонен'),
        ('withdrawn', 'Отозван'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='applications', verbose_name='Заказ')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                  related_name='applications', verbose_name='Исполнитель')
    message = models.TextField('Сообщение')
    proposed_price = models.DecimalField('Предлагаемая цена', max_digits=10, decimal_places=2, 
                                        null=True, blank=True, validators=[MinValueValidator(0)])
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Даты
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    responded_at = models.DateTimeField('Дата ответа', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Отклик'
        verbose_name_plural = 'Отклики'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['order', 'freelancer'], name='unique_application')
        ]
    
    def __str__(self):
        return f'Отклик от {self.freelancer.username} на заказ #{self.order.id}'
    
    def accept(self):
        """Принять отклик"""
        if self.status == 'pending':
            self.status = 'accepted'
            self.responded_at = timezone.now()
            self.save()
            
            # Назначаем исполнителя заказу
            self.order.freelancer = self.freelancer
            self.order.status = 'in_progress'
            self.order.save()
            
            # Отклоняем остальные отклики
            Application.objects.filter(
                order=self.order, 
                status='pending'
            ).exclude(id=self.id).update(status='rejected', responded_at=timezone.now())
            
            # Создаем уведомление для исполнителя
            Notification.objects.create(
                user=self.freelancer,
                title='Ваш отклик принят!',
                message=f'Заказчик принял ваш отклик на заказ "{self.order.title}".',
                notification_type='application_accepted',
                related_object=f'order:{self.order.id}'
            )
            
            return True
        return False
    
    def reject(self):
        """Отклонить отклик"""
        if self.status == 'pending':
            self.status = 'rejected'
            self.responded_at = timezone.now()
            self.save()
            
            # Создаем уведомление для исполнителя
            Notification.objects.create(
                user=self.freelancer,
                title='Отклик отклонен',
                message=f'Заказчик отклонил ваш отклик на заказ "{self.order.title}".',
                notification_type='application_rejected',
                related_object=f'order:{self.order.id}'
            )
            
            return True
        return False
    
    def withdraw(self):
        """Отозвать отклик"""
        if self.status == 'pending':
            self.status = 'withdrawn'
            self.responded_at = timezone.now()
            self.save()
            return True
        return False
    
    @property
    def display_price(self):
        """Отображаемая цена"""
        if self.proposed_price:
            return f"{self.proposed_price} {self.order.get_currency_display()}"
        return f"{self.order.budget} {self.order.get_currency_display()}"


class Notification(models.Model):
    """Уведомление для пользователя"""
    
    NOTIFICATION_TYPES = [
        ('application_received', 'Получен отклик'),
        ('application_accepted', 'Отклик принят'),
        ('application_rejected', 'Отклик отклонен'),
        ('order_assigned', 'Заказ назначен'),
        ('order_completed', 'Заказ завершен'),
        ('order_canceled', 'Заказ отменен'),
        ('message_received', 'Новое сообщение'),
        ('system', 'Системное уведомление'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                            related_name='notifications', verbose_name='Пользователь')
    title = models.CharField('Заголовок', max_length=200)
    message = models.TextField('Сообщение')
    notification_type = models.CharField('Тип уведомления', max_length=50, choices=NOTIFICATION_TYPES)
    related_object = models.CharField('Связанный объект', max_length=100, blank=True, 
                                     help_text='формат: тип:id, например order:15')
    
    # Статус
    is_read = models.BooleanField('Прочитано', default=False)
    is_important = models.BooleanField('Важное', default=False)
    
    # Даты
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    read_at = models.DateTimeField('Дата прочтения', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Уведомление для {self.user.username}: {self.title}'
    
    def mark_as_read(self):
        """Пометить как прочитанное"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    @property
    def object_url(self):
        """URL связанного объекта"""
        if self.related_object:
            obj_type, obj_id = self.related_object.split(':')
            if obj_type == 'order':
                from django.urls import reverse
                return reverse('order:detail', kwargs={'pk': obj_id})
        return None


class OrderFile(models.Model):
    """Файлы, прикрепленные к заказу"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='orders/files/%Y/%m/%d/')
    filename = models.CharField('Название файла', max_length=255)
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Файл заказа'
        verbose_name_plural = 'Файлы заказов'
    
    def __str__(self):
        return self.filename
    


class CancellationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждена'),
        ('rejected', 'Отклонена'),
        ('revoked', 'Отозвана'),
    ]
    
    order = models.OneToOneField(
        'Order',
        on_delete=models.CASCADE,
        related_name='cancellation_request',
        verbose_name='Заказ'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_cancellation_requests',
        verbose_name='Заказчик'
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_cancellation_requests',
        verbose_name='Исполнитель'
    )
    reason = models.TextField(verbose_name='Причина отмены', blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус запроса'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата ответа')
    
    class Meta:
        verbose_name = 'Запрос на отмену'
        verbose_name_plural = 'Запросы на отмену'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Запрос на отмену заказа #{self.order.id}"
    

