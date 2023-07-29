from django.urls import path

from .views import voucher as VoucherView
from .views import auth as AuthView
from .views import user as UserView
from .views import currency as CurrencyView
from .views import payment as PaymentView

urlpatterns = [
	path('auth/register/', AuthView.UserRegister.as_view(), name='register'),
	path('auth/login/', AuthView.UserLogin.as_view(), name='login'),
	path('auth/logout/', AuthView.UserLogout.as_view(), name='logout'),
	path('auth/verify/<str:verification_code>/', AuthView.UserVerificationView.as_view(), name='user-verify'),
	path('auth/resend-verification-code/', AuthView.ResendVerificationCodeView.as_view(), name='resend-verification-code'),
	path('auth/forgot-password/', AuthView.ForgotPasswordView.as_view(), name='forgot-password'),

	path('users/', UserView.UserInfoView.as_view()),
	path('users/update-profile/', UserView.UserProfileUpdateView.as_view()),
	path('users/change-password/', UserView.ChangePasswordView.as_view()),

	path('currency/', CurrencyView.CurrencyListView.as_view()),
	path('currency/rate/', CurrencyView.ExchangeRateView.as_view()),

	path('payment/create/', PaymentView.CreatePaymentView.as_view()),
	path('payment/confirm/', PaymentView.ConfirmPaymentView.as_view()),
    
	path('voucher/balance/', VoucherView.VoucherBalanceView.as_view()),
	path('voucher/redeem/', VoucherView.VoucherRedeemView.as_view()),
]
