from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('aslearn/', views.aslearn, name='aslearn'),
    path('learn/', views.learn, name='learn'),
    path("practice/", views.select_level, name="select_level"),
    path("practice/<str:level>/", views.practice, name="practice"),
    path("practice/<str:level>/next/", views.next_practice, name="next_practice"),
    path("detect_asl/", views.detect_asl, name="detect_asl"),
    path("performance/", views.performance, name="performance"),
]
