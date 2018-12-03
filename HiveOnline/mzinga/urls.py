from django.conf.urls import url, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'games', views.GameViewSet, base_name='games')
router.register(r'new_game', views.NewGame, base_name='new_game')
router.register(r'play_move', views.PlayMove, base_name='play_move')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
