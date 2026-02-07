# order/forms.py (упрощенная версия)
from django import forms
from django.core.validators import MinValueValidator
from .models import Order, Application


class OrderForm(forms.ModelForm):
    """Форма создания и редактирования заказа"""
    files = forms.FileField(
        label='Прикрепить файлы',
        required=False,
        #widget=forms.ClearableFileInput(attrs={'multiple': True})
    )
    
    class Meta:
        model = Order
        fields = ['title', 'description', 'category', 'budget', 'currency', 
                 'deadline', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название заказа'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Подробное описание задачи, требования, сроки...'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Бюджет проекта'
            }),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ключевые слова через запятую'
            }),
        }
        labels = {
            'title': 'Название заказа',
            'description': 'Описание',
            'category': 'Категория',
            'budget': 'Бюджет',
            'currency': 'Валюта',
            'deadline': 'Срок выполнения',
            'tags': 'Теги',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Устанавливаем минимальное значение для бюджета
        self.fields['budget'].validators.append(MinValueValidator(0))
        
        # Устанавливаем минимальную дату дедлайна (завтра)
        if 'deadline' in self.fields:
            import datetime
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            self.fields['deadline'].widget.attrs['min'] = tomorrow.isoformat()
    
    def save(self, commit=True):
        order = super().save(commit=False)
        if self.user:
            order.customer = self.user
        if commit:
            order.save()
        return order


class ApplicationForm(forms.ModelForm):
    """Форма отклика на заказ"""
    
    class Meta:
        model = Application
        fields = ['message', 'proposed_price']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Расскажите о своем опыте и почему вы подходите для этого задания...'
            }),
            'proposed_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Предложите свою цену или оставьте пустым'
            }),
        }
        labels = {
            'message': 'Ваше сообщение',
            'proposed_price': 'Предложенная цена',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поле цены необязательным
        self.fields['proposed_price'].required = False
        self.fields['proposed_price'].validators.append(MinValueValidator(0))
    
    def clean_proposed_price(self):
        """Валидация предложенной цены"""
        proposed_price = self.cleaned_data.get('proposed_price')
        if proposed_price is not None and proposed_price <= 0:
            raise forms.ValidationError("Цена должна быть положительной")
        return proposed_price