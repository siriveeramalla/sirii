from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path("room/<int:room_id>/", views.room_view, name="room"),
    path("create-room/", views.create_room, name="create_room"),
    path("join-room/<int:room_id>/",views.join_room, name="join_room"),
    path("document/<int:room_id>/", views.document_view, name="document"),
    path("save-document/<int:room_id>/", views.save_document, name="save_document"),
    path("get-document/<int:room_id>/", views.get_document, name="get_document"),
    path('get-active-users/<int:room_id>/', views.get_active_users, name='get_active_users'),

]
