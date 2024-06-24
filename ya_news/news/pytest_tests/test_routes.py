from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:home', None),
        ('news:detail', pytest.lazy_fixture('pk_for_args')),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
    )
)
@pytest.mark.django_db
def test_pages_availability_for_anonymous_user(client, news, name, args):
    # Проверка доступности для всех пользователей страниц.
    # Страниц: домашней, отдельной новости, логина, логаута и регистрации.
    url = reverse(name, args=args)  # Получаем ссылку на нужный адрес.
    response = client.get(url)  # Выполняем запрос.
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('admin_client'), HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK)
    ),
)
@pytest.mark.parametrize(
    'name',
    (
        'news:edit',
        'news:delete'
    ),
)
def test_pages_availability_for_different_users(
    parametrized_client, name, comment, expected_status
):
    # Проверим, что автору комментария доступны страницы редактирования
    # и удаления и проверим, что другому пользователю не доступны эти
    # страницы.
    url = reverse(name, args=(comment.pk,))
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


# Тестирование редиректов.
@pytest.mark.parametrize(
    'name',
    (
        'news:edit',
        'news:delete',
    ),
)
def test_redirects(client, name, comment):
    # Проверяем, что анонимного пользователя перенаправляет на страницу
    # логина при попытке редактирования или удаления комментария.
    login_url = reverse('users:login')
    url = reverse(name, args=(comment.pk,))
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
