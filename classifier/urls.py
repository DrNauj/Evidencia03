from django.urls import path
from . import views

urlpatterns = [
    path('', views.predict_customer, name='predict_customer'),
    path('prediction/<int:pk>/', views.prediction_result, name='prediction_result'),
]