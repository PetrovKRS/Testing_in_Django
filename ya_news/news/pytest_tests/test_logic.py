from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertFormError

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

from ya_news.conftest import (
    TEXT_COMMENT,
    TEXT_COMMENT_NEW,
)


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news, form_data):
    # Проверка, что анонимный пользователь не может создать комментарий.
    news_url = reverse('news:detail', args=(news.pk,))
    # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
    # предварительно подготовленные данные формы с текстом комментария.
    client.post(news_url, data=form_data)
    # Считаем количество комментариев.
    comments_count = Comment.objects.count()
    # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
    assert comments_count == 0


@pytest.mark.django_db
def test_user_can_create_comment(author_client, author, news, form_data):
    # Проверка, что авторизованный пользователь может оставить комментарий.
    news_url = reverse('news:detail', args=(news.pk,))
    # Совершаем запрос через авторизованный клиент.
    response = author_client.post(news_url, data=form_data)
    # Проверяем, что редирект привёл к разделу с комментами.
    assertRedirects(response, f'{news_url}#comments')
    comments_count = Comment.objects.count()
    # Убеждаемся, что есть один комментарий.
    assert comments_count == 1
    # Получаем объект комментария из базы.
    comment = Comment.objects.get()
    # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
    assert comment.text == TEXT_COMMENT
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(admin_client, news):
    # Проверка блокировки стоп-слов.
    news_url = reverse('news:detail', args=(news.pk,))
    for bad_word in BAD_WORDS:
        # Формируем данные для отправки формы
        bad_words_data = {'text': f'Какой-то текст, {bad_word}, еще текст'}
        # Отправляем запрос через авторизованный клиент.
        response = admin_client.post(news_url, data=bad_words_data)
        # Проверяем, есть ли в ответе ошибка формы.
        assertFormError(
            response,
            form='form',
            field='text',
            errors=WARNING
        )
    # Дополнительно убедимся, что комментарий не был создан.
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_edit_comment(author_client, news, comment):
    # Проверяем, что автор может отредактировать свой комментарий.
    news_url = reverse('news:detail', args=(news.pk,))
    url_to_comments = news_url + '#comments'
    url_edit = reverse('news:edit', args=(comment.pk,))
    # Выполняем запрос на редактирование от имени автора комментария.
    response = author_client.post(url_edit, data={'text': TEXT_COMMENT_NEW})
    # Проверяем, что сработал редирект.
    assertRedirects(response, url_to_comments)
    # Обновляем объект комментария.
    comment.refresh_from_db()
    # Проверяем, что текст комментария соответствует обновленному.
    assert comment.text == TEXT_COMMENT_NEW


def test_author_can_delete_comment(author_client, news, comment):
    # Проверяем, что автор может удалить свой комментарий.
    news_url = reverse('news:detail', args=(news.pk,))
    url_to_comments = news_url + '#comments'
    url_delete = reverse('news:delete', args=(comment.pk,))
    # От имени автора комментария отправляем DELETE-запрос на удаление.
    response = author_client.delete(url_delete)
    # Проверяем, что редирект привёл к разделу с комментариями.
    # Заодно проверим статус-коды ответов.
    assertRedirects(response, url_to_comments)
    # Считаем количество комментариев в системе.
    comments_count = Comment.objects.count()
    # Ожидаем ноль комментариев в системе.
    assert comments_count == 0


def test_user_cant_edit_comment_of_another_user(admin_client, news, comment):
    # Проверяем, что пользователь не может редактировать чужие комментарии.
    url_edit = reverse('news:edit', args=(comment.pk,))
    # Выполняем запрос на редактирование от имени другого пользователя.
    response = admin_client.post(url_edit, data={'text': 'ABRACADABRA'})
    # Проверяем, что вернулась 404 ошибка.
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Обновляем объект комментария.
    comment.refresh_from_db()
    # Проверяем, что текст остался тем же, что и был.
    assert comment.text == TEXT_COMMENT


def test_user_cant_delete_comment_of_another_user(admin_client, news, comment):
    # Проверяем, что пользователь не может удалить чужой комментарий.
    url_delete = reverse('news:delete', args=(comment.pk,))
    # Выполняем запрос на удаление от пользователя-читателя.
    response = admin_client.delete(url_delete)
    # Проверяем, что вернулась 404 ошибка.
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Убедимся, что комментарий по-прежнему на месте.
    comments_count = Comment.objects.count()
    assert comments_count == 1
