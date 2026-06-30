from django import forms
from django.core.validators import MinValueValidator
from .models import Order, Application, Technology
class OrderForm(forms.ModelForm):
    files = forms.FileField(
        label='Прикрепить файлы',
        required=False,
    )
    technologies = forms.ModelMultipleChoiceField(
        queryset=Technology.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Технологии'
    )

    class Meta:
        model = Order
        fields = ['title', 'description', 'budget', 'currency',
          'deadline', 'tags', 'technologies']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название заказа'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'budget': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ключевые слова через запятую'}),
        }
        labels = {
            'title': 'Название заказа',
            'description': 'Описание',
            'budget': 'Бюджет',
            'currency': 'Валюта',
            'deadline': 'Срок выполнения',
            'tags': 'Теги',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['budget'].validators.append(MinValueValidator(0))
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
            self.save_m2m()  # ← важно для ManyToMany (technologies)
        return order


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['message', 'proposed_price']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'proposed_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'message': 'Ваше сообщение',
            'proposed_price': 'Предложенная цена',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proposed_price'].required = False
        self.fields['proposed_price'].validators.append(MinValueValidator(0))

    def clean_proposed_price(self):
        proposed_price = self.cleaned_data.get('proposed_price')
        if proposed_price is not None and proposed_price <= 0:
            raise forms.ValidationError("Цена должна быть положительной")
        return proposed_price