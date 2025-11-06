from django.shortcuts import render
from django.http import HttpResponse

from goods.models import Categories

def index(request) -> HttpResponse:
    
    categories = Categories.objects.all()
    
    context: dict[str, str] = {
        'title': 'Home',
        'content': 'Магазин мебели HOME',
        'categories': categories
    }
    return render(request, 'main/index.html', context)

def about(request) -> HttpResponse:
    context: dict[str, str] = {
        'title': 'О нас',
        'content': 'О нас тоже',
        'text_on_page': 'Неплохо, хороший товар'
    }
    return render(request, 'main/about.html', context)