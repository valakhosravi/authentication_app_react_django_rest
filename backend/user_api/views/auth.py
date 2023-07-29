import random
import string
from django.contrib.auth import get_user_model, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import UserVerification, AppUser
from ..serializers import ForgotPasswordSerializer, UserRegisterSerializer, UserLoginSerializer
from rest_framework import permissions, status
from ..validations import register_validation, validate_email, validate_password
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
					expire_at=expiration_date
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
					print(f'verification_code: {verification_code}')
					
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
					# send_verification_email(email, verification_code)
					
					return Response({'message': 'A new verification code has been sent to your email.'}, status=status.HTTP_200_OK)
				else:
					return Response({'message': 'User is already verified.'}, status=status.HTTP_400_BAD_REQUEST)
			except AppUser.DoesNotExist:
				return Response({'message': 'User with the provided email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
		else:
			return Response({'message': 'Please provide a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

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