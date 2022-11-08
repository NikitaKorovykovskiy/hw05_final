import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
TEST_POST = 13

User = get_user_model()


class PaginatorViewsTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group'
        )
        count_post: list = []
        for parametr in range(TEST_POST):
            count_post.append(Post(
                text=f'Тестовый текст {parametr}',
                group=self.group,
                author=self.user
            ))
        Post.objects.bulk_create(count_post)

    def test_page_show_correct(self):
        """Проверка количества постов на первой странице. """
        variables = {
            reverse('posts:index'),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
            reverse(
                'posts:group_lists', kwargs={'slug': self.group.slug}
            )
        }
        for page in variables:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_page_show_correct_2(self):
        """Проверка количества постов на второй странице. """
        variables = {
            reverse('posts:index'),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
            reverse(
                'posts:group_lists',
                kwargs={'slug': self.group.slug}
            )
        }
        for page in variables:
            with self.subTest(page=page):
                response = self.guest_client.get(page, {'page': 2})
                self.assertEqual(len(response.context['page_obj']), 3)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.image = uploaded
        cls.user = User.objects.create_user(username='Sazan1')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=Group.objects.create(
                title='Тестовый заголовой',
                slug='test_slug'
            ))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_lists', kwargs={
                    'slug': self.post.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={
                    'username': self.post.author
                }
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={
                    'post_id': self.post.id
                }
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit',
                    args={self.post.id}, ): 'posts/post_create.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_show_correct_context(self):
        """Один пост, отфильтрованный по id"""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        first_object = response.context.get('post')
        self.assertEqual(first_object.text, 'Тестовая запись')
        self.assertEqual(first_object.group.title, 'Тестовый заголовой')
        self.assertEqual(first_object.author.username, 'Sazan1')

    def test_create_edit_show_corrrect_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        """Форма создания поста работает исправно"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            form_field = response.context.get('form').fields.get(value)
            self.assertIsInstance(form_field, expected)

    def test_group_in_pages(self):
        """Проверяем создание поста на нужных страницах"""
        post = Post.objects.create(
            text='Тестовый текст проверка как добавился',
            author=self.user,
            group=self.post.group
        )
        templates_names = {
            reverse('posts:index'): 'поста нет на главной',
            reverse(
                'posts:group_lists',
                kwargs={'slug': post.group.slug}
            ): 'поста нет в профиле',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ): 'поста нет в группе',
        }
        for template, phrase in templates_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                name_of_field = response.context['page_obj']
                self.assertIn(post, name_of_field, phrase)

    def test_control_image_with_paginator(self):
        """Проверка добавление картинки в пост в шаблонах с пагинатором"""
        templates = {
            reverse('posts:index'),
            reverse('posts:group_lists', kwargs={
                'slug': self.post.group.slug
            }),
            reverse('posts:profile', kwargs={'username': self.post.author}),
        }
        for template in templates:
            with self.subTest(tempfile=tempfile):
                response = self.authorized_client.get(template)
                self.assertEqual(
                    response.context.get('page_obj')[0].image, self.post.image
                )

    def test_control_image_without_paginator(self):
        """Проверка добавление картинки в пост в шаблоне без пагинатора"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post').image, self.post.image)
