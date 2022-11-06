from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Практический опыт показывает',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        posts = PostModelTest.post
        expected_object_name = posts.text[:15]
        self.assertEqual(expected_object_name, str(posts))

    def test_models_have_correct_object_group_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        posts = PostModelTest.group
        expected_object_name = posts.title
        self.assertEqual(expected_object_name, str(posts))
