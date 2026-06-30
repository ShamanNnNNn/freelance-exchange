# order/admin.py
from django.contrib import admin
from .models import Order, OrderFile, Application, Notification, CancellationRequest, Technology

class OrderFileInline(admin.TabularInline):
    """Inline для отображения файлов внутри заказа"""
    model = OrderFile
    extra = 0
    fields = ['file', 'uploaded_at']
    readonly_fields = ['uploaded_at']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['title', 'customer', 'budget', 'currency', 
                    'status', 'deadline', 'created_at']
    list_filter = ['status', 'created_at', 'deadline']
    search_fields = ['title', 'description', 'tags', 'customer__username', 
                     'customer__email']
    list_editable = ['status']  # Можно менять статус прямо из списка
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'tags')
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
    
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['order', 'freelancer', 'status', 'proposed_price', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__title', 'freelancer__username', 'message']
    readonly_fields = ['created_at', 'updated_at', 'responded_at']
    list_editable = ['status']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    list_editable = ['is_read']


@admin.register(CancellationRequest)
class CancellationRequestAdmin(admin.ModelAdmin):
    list_display = ['order', 'customer', 'freelancer', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__title', 'customer__username', 'freelancer__username']
    readonly_fields = ['created_at', 'responded_at']
    

@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
