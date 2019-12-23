from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Tag, Ingredient, Recipe
from recipe import serializers


class BaseRecipeAttr(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin):
    """Classe Base"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retornando apenas objetos do usuario"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(user=self.request.user) \
            .order_by('-name').distinct()

    def perform_create(self, serializer):
        """Criando novo objeto"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttr):
    """Gerenciando tags do banco"""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class IngredientsViewSet(BaseRecipeAttr):
    """Geranciando ingredientes do banco"""
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Gerenciando receitas do banco"""
    serializer_class = serializers.RecipeSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def _params_to_ints(qs):
        """Converte uma lista de string ID to int ID list"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Limitar as receitas para o usuario
        autenticado"""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tags_id = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tags_id)
        if ingredients:
            ingredients_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredients_ids)
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """Retorna o serializer correto"""
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Cria uma nova receita"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Faz o upload de uma imagem na receita"""
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
