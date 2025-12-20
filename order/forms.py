# order/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from .models import Order

class OrderForm(forms.ModelForm):
    tags_input = forms.CharField(
        label='Теги',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: дизайн, логотип, брендинг'
        }),
        help_text='Введите ключевые слова через запятую'
    )
    
    # Убираем поле files или делаем одиночный файл
    # files = forms.FileField(
    #     label='Прикрепить файл',
    #     required=False,
    #     widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    # )
    
    class Meta:
        model = Order
        fields = [
            'title',
            'description',
            'category',
            'budget',
            'currency',
            'deadline',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Краткое название проекта'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Подробно опишите задачу, требования и ожидания'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1000',
                'min': '0'
            }),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance.pk:
            self.fields['tags_input'].initial = self.instance.tags
    
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.now().date():
            raise ValidationError('Срок выполнения не может быть в прошлом')
        return deadline
    
    def clean_budget(self):
        budget = self.cleaned_data.get('budget')
        if budget and budget < 0:
            raise ValidationError('Бюджет не может быть отрицательным')
        return budget
    
    def save(self, commit=True):
        order = super().save(commit=False)
        
        if self.user and not order.pk:
            order.customer = self.user
        
        tags_input = self.cleaned_data.get('tags_input', '')
        if tags_input:
            order.tags = tags_input
        
        if commit:
            order.save()
        
        return order