import base64
import os
import uuid

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from api.paginations import Pagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (FavoriteSerializer, FollowSerializer,
                             IngredientSerializer, RecipeReadSerializer,
                             RecipeWriteSerializer, ShoppingCartSerializer,
                             SubscriptionSerializer, UserSerializer)
from recipes.filters import RecipeFilter
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart)
from users.models import Follow

User = get_user_model()


def manage_user_recipe(request, pk, model, serializer_class):
    recipe = get_object_or_404(Recipe, pk=pk)
    
    if request.method == 'POST':
        return _add_recipe(request, recipe, model, serializer_class)
    return _remove_recipe(request, recipe, model)

def _add_recipe(request, recipe, model, serializer_class):
    serializer = serializer_class(data={
        'user': request.user.id,
        'recipe': recipe.id
    })
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)

def _remove_recipe(request, recipe, model):
    item = model.objects.filter(
        user=request.user, recipe=recipe
    ).first()
    if not item:
        return Response(
            {"detail": f"Рецепт не найден в {model._meta.verbose_name}."},
            status=status.HTTP_400_BAD_REQUEST
        )
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    pagination_class = Pagination
    permission_classes = [permissions.AllowAny]

    @action(detail=False,
            methods=['get'],
            permission_classes=[permissions.IsAuthenticated]
            )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False,
            methods=['put', 'delete'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='me/avatar'
            )
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            return self._update_avatar(request, user)
        return self._delete_avatar(request.user)

    def _update_avatar(self, request, user):
        avatar_data = request.data.get('avatar')

        if not avatar_data:
            return Response(
                {"avatar": ["Это поле обязательно."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if user.avatar:
                user.avatar.delete()

            format, imgstr = avatar_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr),
                               name=f"{uuid.uuid4()}.{ext}")

            user.avatar.save(data.name, data, save=True)
            user.save()

            avatar_url = request.build_absolute_uri(user.avatar.url)

            return Response({"avatar": avatar_url},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _delete_avatar(self, user):
        if user.avatar:
            avatar_path = user.avatar.path
            if os.path.exists(avatar_path):
                os.remove(avatar_path)
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"detail": "Аватар отсутствует."},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False,
            methods=['get'],
            url_path='subscriptions',
            permission_classes=[permissions.IsAuthenticated]
            )
    def get_subscriptions(self, request):
        user = request.user

        subscriptions = User.objects.filter(following__user=user)

        page = self.paginate_queryset(subscriptions)

        serializer = FollowSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            methods=['post', 'delete'],
            url_path='subscribe',
            permission_classes=[permissions.IsAuthenticated]
            )
    def manage_subscription(self, request, id=None):
        user = request.user

        if request.method == 'POST':
            return self._subscribe(request, id)
        return self._unsubscribe(request.user, id)

    def _subscribe(self, request, id):
        serializer = SubscriptionSerializer(
            data={'following_id': id},
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        follow = serializer.save()
        return Response(
            FollowSerializer(
                follow.following,
                context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def _unsubscribe(self, user, id):
        following_user = get_object_or_404(User, pk=id)

        follow_instance = Follow.objects.filter(
            user=user, following=following_user).first()

        if not follow_instance:
            return Response(
                {"detail": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly
    ]


class RecipeViewSet(BaseViewSet):
    queryset = Recipe.objects.all().select_related(
        'author').prefetch_related('ingredients')
    pagination_class = Pagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(detail=False,
            methods=['get'],
            url_path='download_shopping_cart',
            permission_classes=[permissions.IsAuthenticated]
            )
    def download_shopping_cart(self, request):
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__shopping_carts__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        
        content = "\n".join(
            [
                f"{ing['ingredient__name']} ({ing['ingredient__measurement_unit']}) — "
                f"{ing['amount']}"
                for ing in ingredients
            ]
        )
        
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def manage_shopping_cart(self, request, pk=None):
        return manage_user_recipe(
            request,
            pk,
            ShoppingCart,
            ShoppingCartSerializer
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=[permissions.IsAuthenticated]
    )
    def manage_favorite(self, request, pk=None):
        return manage_user_recipe(
            request,
            pk,
            Favorite,
            FavoriteSerializer
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (SearchFilter,)
    search_fields = ['name']
    pagination_class = None

    def get_queryset(self):
        name = self.request.query_params.get('name')
        return super().get_queryset().filter(
            name__istartswith=name
        ) if name else super().get_queryset()
