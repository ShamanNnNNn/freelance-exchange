from django.shortcuts import render
from django.http import HttpResponse
from order.models import Order

def index(request) -> HttpResponse:
    open_orders = Order.objects.filter(status='open').select_related('customer')[:6]
    context = {
        'title': 'Фриланс-биржа',
        'open_orders': open_orders,
    }
    return render(request, 'main/index.html', context) 
def about(request) -> HttpResponse:
    context: dict[str, str] = {
        'title': 'О нас',
        'content': 'О нас тоже',
        'text_on_page': 'Неплохо, хороший товар'
    }
    return render(request, 'main/about.html', context)