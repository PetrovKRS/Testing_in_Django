from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()
NOTE_TEXT = 'Text note'
NOTE_TEXT_NEW = 'Text note new'
NOTE_TITLE = 'Title note'
NOTE_SLUG = 'note-slug'
NOTES_COUNT = 10


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Адрес страницы создания заметки.
        cls.url = reverse('notes:add')
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.user = User.objects.create(username='Tester')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # генератор заметок.
        all_notes = [
            Note(
                title=f'{NOTE_TITLE} {index}',
                text=NOTE_TEXT,
                slug=f'{NOTE_SLUG} {index}',
                author=cls.user
            ) for index in range(NOTES_COUNT)
        ]
        Note.objects.bulk_create(all_notes)
        cls.form_data = {
            'title': 'New title',
            'text': NOTE_TEXT_NEW,
            'slug': 'new-slug',
            'author': cls.user
        }

    def test_user_can_create_note(self):
        # Проверяем, что авторизованный пользователь
        # может создать заметку.
        count_notes_before = Note.objects.count()
        response = self.auth_client.post(
            self.url,
            data=self.form_data
        )
        # Проверяем, что был выполнен редирект на страницу
        # успешного добавления заметки.
        self.assertRedirects(response, reverse('notes:success'))
        # Считаем общее количество заметок в БД, ожидаем + 1 заметку.
        self.assertEqual(Note.objects.count(), count_notes_before + 1)
        # Чтобы проверить значения полей заметки -
        # получаем её из базы при помощи метода get():
        new_note = Note.objects.get(slug='new-slug')
        # Сверяем атрибуты объекта с ожидаемыми.
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.user)

    def test_anonymous_user_cant_create_note(self):
        # Проверяем, что анонимный пользователь не может
        # создать заметку. Тест универсален для любого количества
        # заметок в базе.
        # считаем число заметок до попытки создания новой заметки
        count_notes_before = Note.objects.count()
        response = self.client.post(
            self.url,
            data=self.form_data
        )
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.url}'
        # Проверяем, что произошла переадресация на страницу логина:
        self.assertRedirects(response, expected_url)
        # Считаем количество заметок в БД.
        self.assertEqual(Note.objects.count(), count_notes_before)

    def test_empty_slug(self):
        # если при создании заметки оставить поле slug пустым — то
        # содержимое этого поля будет сформировано автоматически, из
        # содержимого поля title. Тест универсален для любого количества
        # заметок в базе.
        count_notes_before = Note.objects.count()
        self.form_data['slug'] = ''
        response = self.auth_client.post(
            self.url,
            data=self.form_data
        )
        # Проверяем, что даже без slug заметка была создана:
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), count_notes_before + 1)
        # Получаем созданную заметку из базы:
        new_note = Note.objects.get(slug=slugify(self.form_data['title']))
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.form_data['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteDelEditSlug(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.author = User.objects.create(username='Author')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Reader')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # генератор заметок.
        all_notes = [
            Note(
                title=f'{NOTE_TITLE} {index}',
                text=NOTE_TEXT,
                slug=f'{NOTE_SLUG} {index}',
                author=cls.author
            ) for index in range(NOTES_COUNT)
        ]
        Note.objects.bulk_create(all_notes)
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=NOTE_TEXT,
            slug=NOTE_SLUG,
            author=cls.author
        )
        # Адрес страницы создания заметки.
        cls.url_add = reverse('notes:add')
        # адрес страницы редактирования заметки.
        cls.url_edit = reverse(
            'notes:edit',
            args=(cls.note.slug,)
        )
        # адрес страницы удаления заметки.
        cls.url_delete = reverse(
            'notes:delete',
            args=(cls.note.slug,)
        )
        cls.form_data = {
            'title': NOTE_TITLE,
            'text': NOTE_TEXT_NEW,
            'slug': NOTE_SLUG,
            'author': cls.author
        }

    def test_not_unique_slug(self):
        # Тестируем возможность создать две заметки с одинаковым
        # slug. Подменяем slug новой заметки на slug уже существующей
        # записи.
        count_notes_before = Note.objects.count()
        self.form_data['slug'] = self.note.slug
        # Пытаемся создать новую заметку:
        response = self.auth_client.post(
            self.url_add,
            data=self.form_data
        )
        # Проверяем, что в ответе содержится ошибка формы для
        # поля slug:
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING)
        )
        # Убеждаемся, что количество заметок в базе осталось равным 1
        self.assertEqual(Note.objects.count(), count_notes_before)

    def test_author_can_edit_note(self):
        # Проверим, что автор может редактировать заметку.
        # В POST-запросе на адрес редактирования заметки
        # отправляем form_data - новые значения для полей заметки:
        response = self.auth_client.post(
            self.url_edit,
            self.form_data
        )
        # Проверяем редирект:
        self.assertRedirects(response, reverse('notes:success'))
        # Обновляем объект заметки note: получаем обновлённые данные из БД:
        self.note.refresh_from_db()
        # Проверяем, что атрибуты заметки соответствуют обновлённым:
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])
        self.assertEqual(self.note.author, self.form_data['author'])

    def test_other_user_cant_edit_note(self):
        # проверяем, что зарегистрированный пользователь не может
        # редактировать чужую заметку.
        response = self.reader_client.post(
            self.url_edit,
            self.form_data
        )
        # Проверяем, что страница не найдена:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Получаем новый объект запросом из БД.
        note_from_db = Note.objects.get(
            pk=self.note.pk
        )
        # Проверяем, что атрибуты объекта из БД равны атрибутам заметки
        # до запроса.
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
        self.assertEqual(self.note.author, note_from_db.author)

    def test_author_can_delete_note(self):
        # Проверяем, что автор может удалить заметку.
        count_notes_before = Note.objects.count()
        response = self.auth_client.post(
            self.url_delete
        )
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), count_notes_before - 1)

    def test_other_user_cant_delete_note(self):
        # Проверяем, что авторизованный пользователь не может удалить
        # чужую заметку.
        count_notes_before = Note.objects.count()
        response = self.reader_client.post(
            self.url_delete
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), count_notes_before)
