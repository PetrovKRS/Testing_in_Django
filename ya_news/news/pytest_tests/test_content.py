import pytest
from django.urls import reverse

from ya_news.yanews.settings import NEWS_COUNT_ON_HOME_PAGE
from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count_on_homepage(client, few_news):
    # Проверяем, что на главной странице отображается не более 10 новостей
    url = reverse('news:home')
    response = client.get(url)
    assert 'object_list' in response.context
    news_count = len(response.context.get('object_list'))
    assert news_count == NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, few_news):
    # Тестируем сортировку новостей.
    url = reverse('news:home')
    response = client.get(url)
    assert 'object_list' in response.context
    object_list = response.context.get('object_list')
    # Получаем даты новостей в том порядке, как они выведены на странице.
    all_dates = [few_news.date for few_news in object_list]
    # Сортируем полученный список по убыванию.
    sorted_dates = sorted(all_dates, reverse=True)
    # Проверяем, что исходный список был отсортирован правильно.
    assert all_dates == sorted_dates


def test_comments_order(client, news, few_comments):
    # Тестируем сортировку комментариев на странице отдельной новости.
    url = reverse('news:detail', args=(news.pk,))
    response = client.get(url)
    # Проверяем, что объект новости находится в словаре контекста
    # под ожидаемым именем - названием модели.
    assert 'news' in response.context
    # Получаем объект новости.
    news = response.context.get('news')
    # Получаем все комментарии к новости.
    all_comments = news.comment_set.all()
    # Проверяем, что время создания первого комментария в списке
    # меньше, чем время создания второго.
    for i in range(1, len(all_comments)):
        assert all_comments[i - 1].created < all_comments[i].created


def test_comment_form_availability_for_user(news, admin_client):
    # Проверяем доступность формы комментария на странице отдельной новости
    # для авторизованного пользователя
    url = reverse('news:detail', args=(news.pk,))
    response = admin_client.get(url)
    assert ('form' in response.context)
    # Проверяем что объект с ключом 'form' в контексте принадлежит
    # классу CommentForm
    assert isinstance(response.context['form'], CommentForm)


def test_comment_form_availability_for_anonymous_user(news, client):
    # Проверяем доступность формы комментария на странице отдельной новости
    # для анонимного пользователя
    url = reverse('news:detail', args=(news.pk,))
    response = client.get(url)
    assert ('form' not in response.context)
