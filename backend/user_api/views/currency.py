from django.contrib.auth import get_user_model, login, logout
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Currency, ExchangeRate
from ..serializers import CurrencySerializer, ExchangeRateSerializer, ExchangeRateUpdateSerializer
from rest_framework import permissions, status
from ..validations import register_validation, validate_email, validate_password
from django.core.mail import send_mail
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

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
		
	def post(self, request):
		serializer = ExchangeRateUpdateSerializer(data=request.data)

		if serializer.is_valid():
			# Check if the API key is provided in the request headers
			api_key = serializer.validated_data['api_key']
			print(api_key)
			if api_key != 'freepfILuW68dnkyVcJTNU53JfqoXEYG':
				return JsonResponse({'error': 'Invalid API key'}, status=401)

			# Parse the request data as JSON
			# data = json.loads(request.body)

			# Get the currency object by name or create it if not exists
			currency_name = serializer.validated_data['currency_name']
			currency, created = Currency.objects.get_or_create(name=currency_name)

			# Get the price from the request data
			price = serializer.validated_data['price']

			# Create the ExchangeRate record
			exchange_rate = ExchangeRate.objects.create(currency=currency, price=price)

			return JsonResponse({'success': True, 'exchange_rate_id': exchange_rate.id})
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CurrencyListView(APIView):
	permission_classes = (permissions.AllowAny,)
	def get(self, request):
		currencies = Currency.objects.all()
		serializer = CurrencySerializer(currencies, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)