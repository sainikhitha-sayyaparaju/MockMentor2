from django.urls import path
from .import views

urlpatterns = [
    path('', views.home, name="home"),
    path('takeInterview', views.takeInterview, name="takeInterview"),
    path('history', views.history, name="history"),
    path('feedback', views.feedback, name="feedback"),
    # path('camera', views.getCam, name="camera"),
    path('video_feed', views.main_interview, name='video_feed'),
    path('checkPosition_video', views.checkPositionVideo, name="checkPosition_video"),
    path('checkPosition', views.checkPosition, name="checkPosition"),
    path('delete_interview/<int:interview_id>/', views.delete_interview, name='delete_interview'),
    path('check_feedback/<int:interview_id>/', views.check_feedback, name='check_feedback'),
]
