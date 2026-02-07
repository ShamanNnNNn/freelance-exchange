from django import forms
from .models import Announcement

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title', 'description', 'category',
            'experience', 'availability',
            'price_per_project', 'currency',
            'skills', 'technologies',
            'contact_email', 'contact_phone', 'telegram',
            'country', 'city',
            'is_active', 'is_premium'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Подробно опишите ваши услуги...'}),
            'experience': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Опишите ваш опыт работы...'}),
            'skills': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Python, Django, JavaScript, HTML, CSS...'}),
            'technologies': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Django 4, React, PostgreSQL...'}),
        }