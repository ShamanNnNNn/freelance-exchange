from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Announcement
from .forms import AnnouncementForm

@login_required
def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.freelancer = request.user
            announcement.save()
            messages.success(request, '✅ Объявление успешно создано!')
            return redirect('announcement:detail', pk=announcement.pk)
    else:
        form = AnnouncementForm()
    
    return render(request, 'create_announcement.html', {'form': form})

@login_required
def my_announcements(request):
    announcements = Announcement.objects.filter(freelancer=request.user).order_by('-created_at')
    return render(request, 'my_announcements.html', {'announcements': announcements})

def all_announcements(request):
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
    
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    if category:
        announcements = announcements.filter(category=category)
    
    if search:
        announcements = announcements.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(skills__icontains=search)
        )
    
    return render(request, 'all_announcements.html', {
        'announcements': announcements,
        'title': 'Все объявления'
    })

def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    
    # УБРАТЬ ИЛИ ЗАКОММЕНТИРОВАТЬ эту часть, так как поля views больше нет:
    # Увеличиваем просмотры только если не владелец
    # if not request.user.is_authenticated or request.user != announcement.freelancer:
    #     announcement.increment_views()
    
    return render(request, 'detail.html', {
        'announcement': announcement,
        'title': announcement.title
    })

@login_required
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, freelancer=request.user)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Объявление успешно обновлено!')
            return redirect('announcement:detail', pk=pk)
    else:
        form = AnnouncementForm(instance=announcement)
    
    return render(request, 'edit_announcement.html', {
        'form': form,
        'announcement': announcement,
        'title': 'Редактировать объявление'
    })

@login_required
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, freelancer=request.user)
    
    if request.method == 'POST':
        announcement.delete()
        messages.success(request, '✅ Объявление успешно удалено!')
        return redirect('announcement:my_announcements')
    
    return render(request, 'delete_announcement.html', {
        'announcement': announcement,
        'title': 'Удалить объявление'
    })

@login_required
def toggle_announcement_status(request, pk):
    """Переключение статуса активности"""
    announcement = get_object_or_404(Announcement, pk=pk, freelancer=request.user)
    announcement.is_active = not announcement.is_active
    announcement.save(update_fields=['is_active'])
    
    status = "активировано" if announcement.is_active else "деактивировано"
    messages.success(request, f'✅ Объявление успешно {status}!')
    
    return redirect('announcement:my_announcements')