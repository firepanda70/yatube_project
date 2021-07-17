from django.shortcuts import render


def index(request):
    template = 'posts/index.html'
    text = 'Это главная страница проекта Yatube'
    title = 'Последние обновления на сайте'
    context = {
        'title': title,
        'text': text
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    title = f'Страница группы {slug}'
    text = 'Здесь будет информация о группах проекта Yatube'
    context = {
        'title': title,
        'text': text
    }
    return render(request, template, context)
