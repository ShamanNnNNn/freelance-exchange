from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from users.models import User

class UserLoginForm(AuthenticationForm):
    
    
    
    username = forms.CharField()
    password = forms.CharField()
    
    class Meta:
        model = User
        fields = ['username', 'password']    
        
    
    
class UserRegistrationForm(UserCreationForm):
    
    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
            )
                
            
            
    
    #username = forms.CharField(label= 'Имя', 
    #                           widget=forms.TextInput(attrs=
    #                                                  {"autofocus": True, 'class': 'form-control', 'placeholder': 'Введите имя пользователя'}))
    #password = forms.CharField(label= 'Пароль', 
    #                           widget=forms.PasswordInput(attrs=
    #                                                      {"autocomplete": "current-password", 'class': 'form-control', 'placeholder': 'Введите пароль'}),)
