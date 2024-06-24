from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author')
        cls.auth_client = Client()

    def test_home_page(self):
        # Проверяем доступность главной страницы анонимному пользователю
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_notes_done_add_for_user_availability(self):
        # Аутентифицированному пользователю доступна страница со списком
        # заметок notes/, страница успешного добавления заметки done/, страница
        # добавления новой заметки add/. Так же проверяем доступность любому
        # пользователю страниц регистрации, входа, выхода из учетной записи.
        self.auth_client.force_login(self.author)
        urls = (
            'notes:list',
            'notes:add',
            'notes:success',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for url in urls:
            url = reverse(url)
            response = self.auth_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)


class TestRoutesDetailDelEdit(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.author = User.objects.create(username='Author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Reader')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Note title',
            text='Note text',
            slug='note-slug',
            author=cls.author
        )

    def test_detail_delete_edit_for_author_availability(self):
        # Страницы отдельной заметки, удаления и редактирования заметки
        # доступны только автору заметки.
        urls = (
            'notes:detail',
            'notes:delete',
            'notes:edit',
        )
        for url in urls:
            url = reverse(url, args=(self.note.slug,))
            response = self.author_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_detail_delete_edit_for_user_not_availability(self):
        # Страницы отдельной заметки, удаления и редактирования заметки не
        # доступны другим пользователям. Если на эти страницы
        # попытается зайти другой пользователь — вернётся ошибка 404.
        urls = (
            'notes:detail',
            'notes:delete',
            'notes:edit',
        )
        for url in urls:
            url = reverse(url, args=(self.note.slug,))
            response = self.reader_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_for_anonymous_client(self):
        # При попытке перейти на страницу списка заметок, страницу
        # успешного добавления записи, страницу добавления заметки,
        # отдельной заметки, редактирования или удаления заметки анонимный
        # пользователь перенаправляется на страницу логина.
        urls = (
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:detail', (self.note.slug,)),
            ('notes:add', None),
            ('notes:list', None),
            ('notes:success', None),
        )
        login_url = reverse('users:login')
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
