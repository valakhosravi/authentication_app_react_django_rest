from django.contrib.auth import get_user_model, login, logout
from rest_framework.authentication import SessionAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Currency, ExchangeRate, UserVerification, AppUser
from .serializers import ChangePasswordSerializer, CurrencySerializer, ExchangeRateSerializer, ForgotPasswordSerializer, UserProfileUpdateSerializer, UserRegisterSerializer, UserLoginSerializer, UserSerializer
from rest_framework import permissions, status
from .validations import register_validation, validate_email, validate_password
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from django.utils import timezone
from django.core.mail import send_mail, BadHeaderError
from django.core.exceptions import ValidationError
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
import random
import string

UserModel = get_user_model()

class UserRegister(APIView):
	permission_classes = (permissions.AllowAny,)

	@swagger_auto_schema(request_body=UserRegisterSerializer)
	def post(self, request):
		clean_data = register_validation(request.data)
		serializer = UserRegisterSerializer(data=clean_data)
		if serializer.is_valid(raise_exception=True):
			user = serializer.create(clean_data)
			if user:
				# Generate a verification code
				verification_code = get_random_string(length=6)

				# Calculate expiration date (one day from now)
				expiration_date = timezone.now() + timezone.timedelta(days=1)

				# Create a UserVerification instance and associate it with the user
				user_verification = UserVerification.objects.create(
					user=user,
					code=verification_code,
					expire_at=expiration_date  # Set the expiration date based on your logic
				)

				# Send the verification code via email
				# send_verification_email(user.email, verification_code)

				return Response(serializer.data, status=status.HTTP_201_CREATED)

		return Response(status=status.HTTP_400_BAD_REQUEST)

def send_verification_email(email, verification_code):
	subject = 'Verification Code'
	message = f'Your verification code is: {verification_code}'
	from_email = 'account@s-pay.click'
	recipient_list = [email]
		
	try:
		send_mail(subject, message, from_email, recipient_list)
	except BadHeaderError as e:
		print(f"BadHeaderError: {e}")
	except ValidationError as e:
		print(f"ValidationError: {e}")
	except Exception as e:
		print(f"Error: {e}")


class UserLogin(APIView):
	permission_classes = (permissions.AllowAny,)

	@swagger_auto_schema(request_body=UserLoginSerializer)
	def post(self, request):
		data = request.data
		assert validate_email(data)
		assert validate_password(data)
		serializer = UserLoginSerializer(data=data)
		if serializer.is_valid(raise_exception=True):
			user = serializer.check_user(data)
			
			# Check if the user is verified
			if not user.is_verified:
				raise AuthenticationFailed("User is not verified. Please complete the verification process.")
			
			# Log in the user
			login(request, user)

			# Get or create the session token
			token, created = Token.objects.get_or_create(user=user)

			# Include the session token in the response data
			response_data = serializer.data
			response_data['session_token'] = token.key

			return Response(response_data, status=status.HTTP_200_OK)


class UserLogout(APIView):
	permission_classes = (permissions.AllowAny,)
	authentication_classes = (TokenAuthentication,)

	def post(self, request):
		# Retrieve the user's token from the request headers
		auth_header = request.headers.get('Authorization')
		print(auth_header)
		if auth_header and auth_header.startswith('Token '):
			token_key = auth_header.split('Token ')[1]

			try:
				# Get the token object from the database
				token = Token.objects.get(key=token_key)

				# Delete the token from the database
				token.delete()

				# Log out the user
				logout(request)

				return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
			except Token.DoesNotExist:
				return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error': 'Authorization header with Token not provided.'}, status=status.HTTP_400_BAD_REQUEST)


class UserVerificationView(APIView):
	permission_classes = (permissions.AllowAny,)
	authentication_classes = ()
	def get(self, request, verification_code):
		try:
			# Retrieve the UserVerification instance based on the verification code
			user_verification = UserVerification.objects.get(code=verification_code)

			# Check if the verification code has not expired
			if user_verification.expire_at >= timezone.now():
				# Update the associated AppUser's is_verified field to True
				user_verification.user.is_verified = True
				user_verification.user.save()

				# Delete the UserVerification instance as it's no longer needed
				user_verification.delete()

				return Response({'message': 'User has been verified successfully.'}, status=status.HTTP_200_OK)
			else:
				# If the verification code has expired, return an error response
				return Response({'message': 'Verification code has expired.'}, status=status.HTTP_400_BAD_REQUEST)
		except UserVerification.DoesNotExist:
			# If the verification code is invalid, return an error response
			return Response({'message': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationCodeView(APIView):

	permission_classes = (permissions.AllowAny,)
	authentication_classes = ()
	
	def post(self, request):
		email = request.data.get('email')
		
		if email:
			try:
				# Check if the user exists based on the provided email
				user = AppUser.objects.get(email=email)
				
				# Check if the user is not already verified
				if not user.is_verified:
					# Generate a new verification code
					verification_code = get_random_string(length=6)
					
					# Calculate expiration date (one day from now)
					expiration_date = timezone.now() + timezone.timedelta(days=1)
					
					# Create a new UserVerification instance or update the existing one
					user_verification, created = UserVerification.objects.get_or_create(
						user=user,
						defaults={
							'code': verification_code,
							'expire_at': expiration_date
						}
					)
					
					if not created:
						# If the UserVerification instance already exists, update its code and expiration date
						user_verification.code = verification_code
						user_verification.expire_at = expiration_date
						user_verification.save()
					
					# Send the new verification code via email
					send_verification_email(email, verification_code)
					
					return Response({'message': 'A new verification code has been sent to your email.'}, status=status.HTTP_200_OK)
				else:
					return Response({'message': 'User is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
			except AppUser.DoesNotExist:
				return Response({'message': 'User with the provided email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
		else:
			return Response({'message': 'Please provide a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

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
			'created_at': user.created_at,
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
		

class ForgotPasswordView(APIView):
	permission_classes = (permissions.AllowAny,)

	@swagger_auto_schema(request_body=ForgotPasswordSerializer)
	def post(self, request):
		serializer = ForgotPasswordSerializer(data=request.data)
		
		if serializer.is_valid():
			email = serializer.validated_data['email']

			try:
				# Retrieve the user based on the provided email
				user = UserModel.objects.get(email=email)
				
				# Generate a random password
				random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

				print(f"Random password: {random_password}")

				# Set the random password for the user and save it
				user.set_password(random_password)
				user.save()

				# Send the random password via email
				# send_mail(
				# 	'Password Reset',
				# 	f'Your new password is: {random_password}',
				# 	'noreply@example.com',
				# 	[email],
				# 	fail_silently=False,
				# )

				return Response({'message': 'An email with the new password has been sent.'}, status=status.HTTP_200_OK)
			except UserModel.DoesNotExist:
				return Response({'error': 'User with the provided email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		

class ExchangeRateView(APIView):
    permission_classes = (permissions.AllowAny,)
    
    @swagger_auto_schema(query_serializer=ExchangeRateSerializer)
    def get(self, request):
        serializer = ExchangeRateSerializer(data=request.query_params)
        
        if serializer.is_valid():
            currency_name = serializer.validated_data['currency_name']

            try:
                # Get the latest exchange rate for the provided currency name
                currency = Currency.objects.get(name=currency_name)
                latest_exchange_rate = ExchangeRate.objects.filter(currency=currency).latest('create_at')

                return Response({
                    'currency_name': currency_name,
                    'price': latest_exchange_rate.price,
                    'create_at': latest_exchange_rate.create_at,
                }, status=status.HTTP_200_OK)
            except Currency.DoesNotExist:
                return Response({'error': 'Currency with the provided name does not exist.'}, status=status.HTTP_404_NOT_FOUND)
            except ExchangeRate.DoesNotExist:
                return Response({'error': 'Exchange rate for the provided currency name does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CurrencyListView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request):
        currencies = Currency.objects.all()
        serializer = CurrencySerializer(currencies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)