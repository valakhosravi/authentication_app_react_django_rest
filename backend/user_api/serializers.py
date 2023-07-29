from django.forms import ValidationError
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

from .models import Currency, Payment, Transaction, Voucher

UserModel = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserModel
		fields = '__all__'
	def create(self, validated_data):
		# Extract the additional fields from the validated data
		phone_number = validated_data.pop('phone_number')
		first_name = validated_data.pop('first_name')
		last_name = validated_data.pop('last_name')

		# Create the user object with the remaining validated data
		user_obj = UserModel.objects.create_user(email=validated_data['email'], password=validated_data['password'])

		# Set the additional fields on the user object and save it
		user_obj.phone_number = phone_number
		user_obj.first_name = first_name
		user_obj.last_name = last_name
		user_obj.save()

		return user_obj


class UserProfileUpdateSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserModel
		fields = ['phone_number', 'first_name', 'last_name']

class UserLoginSerializer(serializers.Serializer):
	email = serializers.EmailField()
	password = serializers.CharField()
	##
	def check_user(self, clean_data):
		user = authenticate(username=clean_data['email'], password=clean_data['password'])
		if not user:
			raise ValidationError('user not found')
		return user

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserModel
		fields = ('email')

class ChangePasswordSerializer(serializers.Serializer):
	old_password = serializers.CharField(required=True)
	new_password = serializers.CharField(required=True)	
		
class ForgotPasswordSerializer(serializers.Serializer):
	email = serializers.EmailField()
		
class ExchangeRateSerializer(serializers.Serializer):
	currency_name = serializers.CharField(max_length=100)

class ExchangeRateUpdateSerializer(serializers.Serializer):
	api_key = serializers.CharField(max_length=100)
	currency_name = serializers.CharField(max_length=100)
	price = serializers.DecimalField(max_digits=20, decimal_places=2)

class CurrencySerializer(serializers.ModelSerializer):
	class Meta:
		model = Currency
		fields = '__all__'

class VoucherSerializer(serializers.ModelSerializer):
	class Meta:
		model = Voucher
		fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
	class Meta:
		model = Payment
		fields = '__all__'
		
class VoucherSerializer(serializers.ModelSerializer):
	class Meta:
		model = Voucher
		fields = ('code', 'amount', 'expire_at', 'is_used')
		
class VoucherBalanceRequestSerializer(serializers.Serializer):
	api_key = serializers.CharField(max_length=100)
	voucher_code = serializers.CharField(max_length=16)

class VoucherRedeemRequestSerializer(serializers.Serializer):
	api_key = serializers.CharField(max_length=100)
	voucher_code = serializers.CharField(max_length=16)
	amount = serializers.DecimalField(max_digits=20, decimal_places=2)

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        exclude = ['id']