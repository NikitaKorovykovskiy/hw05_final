import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Byblik')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое поле'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текс исходный',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {'text': 'Новый текст', 'group': self.group.id}
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        posts = Post.objects.order_by('id').last()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(posts.text, form_data['text'])
        self.assertEqual(posts.group.id, form_data['group'])
        self.assertEqual(posts.author, self.post.author)
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_post_edit(self):
        """Валидная форма меняет запись и группу"""
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.user,
            group=self.group
        )
        self.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test_group',
            description='Описание'
        )
        post_count = Post.objects.count()
        form_data = {'text': 'Изменяем текст', 'group': self.group2.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        posts = Post.objects.get(pk=self.post.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(posts.text, form_data['text'])
        self.assertEqual(posts.group.id, self.group2.id)

    def test_create_group_post_form(self):
        """При отправке поста с картинкой создается запись в БД"""
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Тест',
            'group': self.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.image, 'posts/small.gif')
