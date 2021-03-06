from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
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

    def test_create_ingredient_successful(self):
        """Testando a criação de um novo ingrediente"""
        payload = {'name': 'meat'}
        res = self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_invalid_ingredient(self):
        """Testa que não é póssivel criar ingrediente invalido"""
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredientes_assigned_recipes(self):
        """Testa o filtro de ingredientes associadas a uma receita"""
        ingredient1 = Ingredient.objects.create(
            user=self.user, name='Apples'
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user, name='Turkey'
        )
        recipe = Recipe.objects.create(
            title='Apple crumble',
            time_minutes=5,
            price=10.00,
            user=self.user
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredientes_assigned_unique(self):
        """Retorna ingredientes associados unicos"""
        ingredient = Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Cheese')

        recipe1 = Recipe.objects.create(
            title='Eggs Benedicts',
            time_minutes=20,
            price=12.00,
            user=self.user
        )
        recipe1.ingredients.add(ingredient)
        recipe2 = Recipe.objects.create(
            title='Eggs toast',
            time_minutes=20,
            price=12.00,
            user=self.user
        )
        recipe2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
