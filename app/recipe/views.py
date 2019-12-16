from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Ingredient
from recipe import serializers


class BaseRecipeAttr(viewsets.GenericViewSet,
                     mixins.ListModelMixin,
                     mixins.CreateModelMixin):
    """Classe Base"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Retornando apenas objetos do usuario"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

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