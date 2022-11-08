from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Post, User


class CommentsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Byblik')
        cls.post = Post.objects.create(
            text='Редактируемый текст',
            author=cls.user,
        )
        cls.comment_url = reverse(
            'posts:add_comment', kwargs={'post_id': cls.post.id}
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_comment(self):
        """Только авторизированный пользователь может комментировать"""
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post.id}
            ),
            data=form_data,
        )
        comment = Comment.objects.filter(post=CommentsTest.post).last()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, CommentsTest.post)
        self.assertEqual(comment.author, CommentsTest.user)

    def test_comment_show_on_profile(self):
        """После отправки коммент показывается на странице поста"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True,
        )
        comment = Comment.objects.first()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(comment.text, form_data['text'])
