from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User, Follow, Comment

User = get_user_model()


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Автор постов
        cls.user_1 = User.objects.create_user(username='User1')
        # Подписчик
        cls.user_2 = User.objects.create_user(username='User2')
        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user_1
        )
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_group_1'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_group_2'
        )
        cls.post = Post.objects.create(
            text='Новый текст поста',
            author=cls.user_1,
            group=cls.group_1
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Отлично',
            author=cls.user_1
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)

    def test_follow_user(self):
        """Авторизованный пользователь,
        может подписываться на других пользователей"""
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user_2})
        )
        follow = Follow.objects.filter(
            user=self.user_1, author=self.user_2
        ).last()
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.user, self.user_1)

    def test_new_post_follow(self):
        """ Новая запись пользователя будет в ленте у тех кто на него
            подписан.
        """
        following = User.objects.create(username='Author_posts')
        Follow.objects.create(user=self.user_1, author=following)
        post = Post.objects.create(author=following, text=self.post.text)
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(post, response.context['page_obj'])
