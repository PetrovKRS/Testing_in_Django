from datetime import timedelta, datetime
from math import sin

import pytest
from django.utils import timezone

from news.models import Comment, News

# Константа для текста комментария
TEXT_COMMENT = 'Text comment'
# Константа для текста нового комментария
TEXT_COMMENT_NEW = 'Text comment new'
# Константа для текста новости
TEXT_NEWS = 'Text news'


@pytest.fixture
def form_data():
    form_comment = {
        'text': TEXT_COMMENT,
    }
    return form_comment


@pytest.fixture
# Используем встроенную фикстуру для модели пользователей django_user_model.
def author(django_user_model):
    return django_user_model.objects.create(username='Tester')


@pytest.fixture
def author_client(author, client):  # Вызываем фикстуру автора и клиента.
    client.force_login(author)  # Логиним автора в клиенте.
    return client


@pytest.fixture
def few_news(author):
    today = datetime.today()
    # Генератор новостей
    all_news = [
        News(
            title=f'Новость {index}',
            text=TEXT_NEWS,
            # Для каждой новости уменьшаем дату на index дней от today
            date=today - timedelta(days=index)
        )
        for index in range(10 + 1)
    ]
    return News.objects.bulk_create(all_news)


@pytest.fixture
def few_comments(author, news):
    now = timezone.now()
    # Генератор комментариев
    all_comments = (
        Comment(
            news=news,
            author=author,
            text=TEXT_COMMENT,
            created=now + timedelta(days=int(100 * abs(sin(1))))
        )
        for index in range(10)
    )
    return Comment.objects.bulk_create(all_comments)


@pytest.fixture
def news(author):
    news = News.objects.create(  # Создаём объект заметки.
        title='Title',
        text=TEXT_NEWS,
    )
    return news


@pytest.fixture
def comment(author, news):
    comment = Comment.objects.create(  # Создаем объект комментария
        news=news,
        author=author,
        text=TEXT_COMMENT
    )
    return comment


@pytest.fixture
# Фикстура запрашивает другую фикстуру создания заметки.
def pk_for_args(news):
    # И возвращает кортеж, который содержит pk новости.
    # На то, что это кортеж, указывает запятая в конце выражения.
    return (news.pk, )
