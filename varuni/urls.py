from django.urls import path
from . import views
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK", status=200)

urlpatterns = [
     path("healthz/", health_check),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),
    path('room/<int:room_id>/', views.room_view, name='room'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/<int:room_id>/', views.join_room, name='join_room'),
    path('document/<int:room_id>/', views.document_view, name='document'),
    path('save-document/<int:room_id>/', views.save_document, name='save_document'),
    path('get-document/<int:room_id>/', views.get_document, name='get_document'),
    path('get-active-users/<int:room_id>/', views.get_active_users, name='get_active_users'),
    path('update-editing-status/<int:room_id>/', views.update_editing_status, name='update_editing_status'),
    path('get-editing-users/<int:room_id>/', views.get_editing_users, name='get_editing_users'),
    path('logout-room/<str:room_id>/', views.logout_room_users, name='logout_room_users'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('export/docx/<str:room_id>/', views.export_docx, name='export_docx'),
    path('export/pdf/<str:room_id>/', views.export_pdf, name='export_pdf'),
    path('share-document/<int:room_id>/', views.share_document, name='share_document'),
    path('invite/<int:room_id>/', views.invite_user, name='invite_user'),
    path('join/<int:room_id>/', views.join_document, name='join_document'),
     path('access_via_email/', views.access_via_email, name='access_via_email'),
    path('signup_custom/', views.signup_custom, name='signup_custom'),
]
