# order/admin.py
from django.contrib import admin
from .models import Order, OrderFile

class OrderFileInline(admin.TabularInline):
    """Inline для отображения файлов внутри заказа"""
    model = OrderFile
    extra = 0
    fields = ['file', 'uploaded_at']
    readonly_fields = ['uploaded_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'category', 'budget', 'currency', 
                    'status', 'deadline', 'created_at']
    list_filter = ['status', 'category', 'created_at', 'deadline']
    search_fields = ['title', 'description', 'tags', 'customer__username', 
                     'customer__email']
    list_editable = ['status']  # Можно менять статус прямо из списка
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'category', 'tags')
        }),
        ('Бюджет и сроки', {
            'fields': ('budget', 'currency', 'deadline')
        }),
        ('Участники и статус', {
            'fields': ('customer', 'freelancer', 'status')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [OrderFileInline]
    
    def get_queryset(self, request):
        """Переопределяем queryset для отображения всех заказов"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Для обычных пользователей показываем только их заказы
        return qs.filter(customer=request.user)

@admin.register(OrderFile)
class OrderFileAdmin(admin.ModelAdmin):
    list_display = ['order', 'file', 'uploaded_at']
    list_filter = ['uploaded_at', 'order__status']
    search_fields = ['order__title', 'file']
    readonly_fields = ['uploaded_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Для обычных пользователей показываем только их файлы
        return qs.filter(order__customer=request.user)