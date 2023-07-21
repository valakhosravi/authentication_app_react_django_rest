from django.urls import path
from . import views

urlpatterns = [
	path('auth/register', views.UserRegister.as_view(), name='register'),
	path('auth/login', views.UserLogin.as_view(), name='login'),
	path('auth/logout', views.UserLogout.as_view(), name='logout'),
    path('auth/verify/<str:verification_code>/', views.UserVerificationView.as_view(), name='user-verify'),
	path('auth/resend-verification-code/', views.ResendVerificationCodeView.as_view(), name='resend-verification-code'),
	path('auth/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    
	path('user/', views.UserInfoView.as_view()),
    path('user/update-profile', views.UserProfileUpdateView.as_view()),
    path('user/change-password/', views.ChangePasswordView.as_view()),
    
    path('currency/', views.CurrencyListView.as_view()),
	path('currency/rate/', views.ExchangeRateView.as_view()),
]
