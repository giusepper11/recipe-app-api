from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientsAPITests(TestCase):
    """Testando ingredientes sem autenticacao"""

    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        """Testa que o login é necessario para acessar"""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """testando os se eh possivel obter ingredientes autenticado"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='teste@gmail.com',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """testa se obtemos uma lista de ingredientes"""
        Ingredient.objects.create(user=self.user, name='Batata')
        Ingredient.objects.create(user=self.user, name='Sal')

        res = self.client.get(INGREDIENTS_URL)

        ingredientes = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredientes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """testa q apenas os ingredientes do usuario apareca"""
        user2 = get_user_model().objects.create_user(
            'other@email.com', 'testpas22')
        Ingredient.objects.create(user=user2, name='Batata')
        ingredient = Ingredient.objects.create(user=self.user, name='Sal')

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
