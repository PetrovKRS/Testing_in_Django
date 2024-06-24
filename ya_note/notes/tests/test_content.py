from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestNotesList(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Адрес страницы создания заметки.
        cls.url = reverse('notes:list')
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.author = User.objects.create(username='Author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note_author = Note.objects.create(
            title='Author_title',
            text='Note text',
            slug='author-slug',
            author=cls.author
        )
        cls.reader = User.objects.create(username='Reader')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note_reader = Note.objects.create(
            title='Reader_title',
            text='Note text',
            slug='reader-slug',
            author=cls.reader
        )

    def test_notes_list_for_different_users(self):
        # Проверяем, что отдельная заметка передаётся на страницу со
        # списком заметок. Проверяем, что в список заметок одного
        # пользователя не попадают заметки другого пользователя.
        users_notes = (
            (self.author_client, self.note_author),
            (self.reader_client, self.note_reader),
        )
        for user, note in users_notes:
            with self.subTest(user=user, note=note):
                response = user.get(self.url)
                self.assertIn('object_list', response.context)
                object_list = response.context.get('object_list')
                # Проверяем, что заметка автора есть в списке
                self.assertIn(note, object_list)

    def test_pages_contains_form(self):
        # Проверяем, что на страницы создания и редактирования заметки
        # передаются формы.
        urls = (
            ('notes:edit', (self.note_author.slug,)),
            ('notes:add', None),
        )
        for name, args in urls:
            with self.subTest(mane=name):
                response = self.author_client.get(reverse(name, args=args))
                # Проверяем, есть ли объект формы в словаре контекста:
                self.assertIn('form', response.context)
                # Проверяем что объект с ключом 'form' в контексте принадлежит
                # классу NoteForm
                self.assertIsInstance(response.context['form'], NoteForm)
