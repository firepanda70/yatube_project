from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import ELEMENTS_PER_PAGE

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group').all()
    paginator = Paginator(posts, ELEMENTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, ELEMENTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'group': group,
        'page': page
    }
    return render(request, template, context)


def profile(request, username):
    user = request.user
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, ELEMENTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    try:
        Follow.objects.get(user=user, author=author)
    except ObjectDoesNotExist:
        pass
    except MultipleObjectsReturned:
        following = True
    else:
        following = True
    finally:
        context = {
            'author': author,
            'page': page,
            'following': following
        }
        return render(request, template, context)


def post_detail(request, username, post_id):
    template = 'posts/post_detail.html'
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts, pk=post_id)
    if request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            Comment.objects.create(
                post=post,
                text=form.cleaned_data['text'],
                author=request.user,
            )
    form = CommentForm()
    context = {
        'author': author,
        'post': post,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            Post.objects.create(
                text=form.cleaned_data['text'],
                author=request.user,
                group=form.cleaned_data['group'],
                image=form.cleaned_data['image']
            )
            return redirect('posts:index')
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts, pk=post_id)
    if request.user != author:
        return redirect('posts:post_detail', author.username, post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.POST and form.is_valid():
        form.save()
        return redirect('posts:post_detail', author.username, post_id)
    return render(request, 'posts/create_post.html',
                  {'is_edit': True, 'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    template = 'posts/comment.html'
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts, pk=post_id)
    if request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            Comment.objects.create(
                post=post,
                text=form.cleaned_data['text'],
                author=request.user,
            )
        return redirect('posts:post_detail', author.username, post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def follow_index(request):
    user = request.user
    authors = []
    for follow in Follow.objects.filter(user=user):
        authors.append(follow.author)
    posts = Post.objects.filter(author__in=authors)
    paginator = Paginator(posts, ELEMENTS_PER_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        if not Follow.objects.filter(user=user, author=author).exists():
            Follow.objects.create(
                user=user,
                author=author
            )
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:follow_index')


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
