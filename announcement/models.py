# announcement/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Announcement(models.Model):
    CATEGORY_CHOICES = [
        ('web', 'Веб-разработка'),
        ('mobile', 'Мобильная разработка'),
        ('design', 'Дизайн'),
        ('marketing', 'Маркетинг'),
        ('content', 'Контент'),
        ('other', 'Другое'),
    ]
    
    EMPLOYMENT_CHOICES = [
        ('full', 'Полная занятость'),
        ('part', 'Частичная занятость'),
        ('project', 'Проектная работа'),
        ('freelance', 'Фриланс'),
    ]
    
    CURRENCY_CHOICES = [
        ('RUB', 'Рубли'),
        ('USD', 'Доллары'),
        ('EUR', 'Евро'),
    ]

    # Основные поля
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Описание')
    category = models.CharField('Категория', max_length=50, choices=CATEGORY_CHOICES)
    
    # Связи
    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        related_name='announcements'
    )
    
    
    # Условия работы
    experience = models.TextField('Опыт работы', blank=True)
    availability = models.CharField('Доступность', max_length=100, default='Готов к работе')
    

    price_per_project = models.DecimalField('Цена за проект', max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField('Валюта', max_length=3, choices=CURRENCY_CHOICES, default='RUB')
    
    # Навыки
    skills = models.TextField('Навыки', help_text='Перечислите через запятую')
    technologies = models.TextField('Технологии', blank=True)
    
    # Контакты
    contact_email = models.EmailField('Email для связи', null=True, blank=True)
    contact_phone = models.CharField('Телефон', max_length=20, null=True, blank=True)
    telegram = models.CharField('Telegram', max_length=100, null=True, blank=True)
    
    # Локация
    country = models.CharField('Страна', max_length=100, blank=True)
    city = models.CharField('Город', max_length=100, blank=True)
    
    # Статус
    is_active = models.BooleanField('Активно', default=True)
    is_premium = models.BooleanField('Премиум', default=False)
    # УДАЛИТЬ ЭТУ СТРОКУ: views = models.PositiveIntegerField('Просмотры', default=0)
    
    # Даты
    created_at = models.DateTimeField('Дата создания', default=timezone.now)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
    
    def __str__(self):
        return f"{self.title} - {self.freelancer.username}"
    
    # УДАЛИТЬ ЭТУ ФУНКЦИЮ:
    # def increment_views(self):
    #     self.views += 1
    #     self.save(update_fields=['views'])
    
    def skills_list(self):
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('announcement:detail', kwargs={'pk': self.pk})