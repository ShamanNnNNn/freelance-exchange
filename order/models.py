from django.db import models
from django.conf import settings  # Добавляем импорт settings
from django.core.validators import MinValueValidator

class Order(models.Model):
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
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
    
    CURRENCY_CHOICES = [
        ('RUB', '₽ Рубли'),
        ('USD', '$ Доллары'),
        ('EUR', '€ Евро'),
    ]
    
    # Основная информация
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Подробное описание')
    category = models.CharField('Категория', max_length=50, choices=CATEGORY_CHOICES)
    
    # Бюджет и сроки
    budget = models.DecimalField(
        'Бюджет',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField('Валюта', max_length=3, choices=CURRENCY_CHOICES, default='RUB')
    deadline = models.DateField('Срок выполнения')
    
    # Статус и связи
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Используем AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Заказчик'
    )
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Используем AUTH_USER_MODEL
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders',
        verbose_name='Исполнитель'
    )
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    
    # Дополнительные поля
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    # Тэги
    tags = models.CharField('Теги', max_length=500, blank=True, help_text='Укажите через запятую')
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class OrderFile(models.Model):
    """Отдельная модель для файлов заказа"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='Заказ'
    )
    file = models.FileField(
        'Файл',
        upload_to='order_files/%Y/%m/%d/'
    )
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Файл заказа'
        verbose_name_plural = 'Файлы заказа'
    
    def __str__(self):
        return f"Файл для заказа {self.order.title}"
    
    class Meta:
        verbose_name = 'Файл заказа'
        verbose_name_plural = 'Файлы заказа'
    
    def __str__(self):
        return f"Файл для заказа {self.order.title}"