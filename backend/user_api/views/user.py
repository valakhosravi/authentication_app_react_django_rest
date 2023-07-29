from django.contrib.auth import get_user_model, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from ..serializers import ChangePasswordSerializer, CurrencySerializer, ExchangeRateSerializer, ExchangeRateUpdateSerializer, ForgotPasswordSerializer, PaymentSerializer, UserProfileUpdateSerializer, UserRegisterSerializer, UserLoginSerializer, UserSerializer, VoucherSerializer
from rest_framework import permissions, status
from ..validations import register_validation, validate_email, validate_password
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authentication import TokenAuthentication

class UserInfoView(APIView):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (permissions.IsAuthenticated,)

	def get(self, request):
		# The user is already authenticated by TokenAuthentication
		# You can access the authenticated user using request.user

		# Retrieve the user's information from the database
		user = request.user

		# You can access user attributes like username, email, etc.
		user_info = {
			'first_name': user.first_name,
			'last_name': user.last_name,
			'phone_number': user.phone_number,
			'email': user.email,
			'is_active': user.is_active,
			'is_verified': user.is_verified,
			'create_at': user.create_at,
			'updated_at': user.updated_at,
		}

		return Response(user_info, status=status.HTTP_200_OK)

class UserProfileUpdateView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def put(self, request):
		user = request.user
		serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)

		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_200_OK)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
	authentication_classes = (TokenAuthentication,)
	permission_classes = (permissions.IsAuthenticated,)

	@swagger_auto_schema(request_body=ChangePasswordSerializer)
	def post(self, request):
		serializer = ChangePasswordSerializer(data=request.data)

		if serializer.is_valid():
			user = request.user
			old_password = serializer.validated_data['old_password']
			new_password = serializer.validated_data['new_password']

			# Check if the old password matches the user's current password
			if not user.check_password(old_password):
				return Response({'error': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

			# Set the new password and save the user object
			user.set_password(new_password)
			user.save()

			return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)