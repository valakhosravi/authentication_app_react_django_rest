import uuid
from rest_framework import status
from rest_framework.response import Response
from ..models import Payment, Voucher
from ..serializers import PaymentSerializer, VoucherSerializer
from django.core.mail import send_mail
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema


class CreatePaymentView(APIView):
	def post(self, request):
		# Process payment details from request data (e.g., amount, payment method)
		serializer = PaymentSerializer(data=request.body)
		if serializer.is_valid():
			amount = request.data.get('amount')
			payment_method = request.data.get('payment_method')

			# Assuming you have already authenticated the user, get the user from the request or using the authentication
			user = request.user

			# Create a new Payment object
			payment = Payment.objects.create(
				user=user,
				amount=amount,
				payment_method=payment_method
			)

			# Save the Payment object
			payment_serializer = PaymentSerializer(payment)

			return Response(data=payment_serializer.data, status=status.HTTP_201_CREATED)
		else:
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConfirmPaymentView(APIView):
	def post(self, request):
		# Process PayPal payment confirmation and update Payment object status
		payment_id = request.data.get('payment_id')
		# You should implement the PayPal integration using 'paypalrestsdk' or other libraries
		# Here, we are assuming that you have implemented a function to verify the PayPal payment status

		# Verify the PayPal payment status
		is_successful = self.verify_paypal_payment(payment_id)

		if is_successful:
			try:
				# Get the payment associated with the given PayPal payment ID
				payment = Payment.objects.get(pk=payment_id)

				# Update the Payment object status to successful
				payment.is_successful = True
				payment.save()

				# Create vouchers for the user's basket items and save them
				vouchers = []
				vouchers_in_basket = request.data.get('vouchers')
				for basket_item in vouchers_in_basket: # TODO: Think about the user basket
					value = self.generate_unique_voucher_code()
					voucher = Voucher.objects.create(
						amount=basket_item.amount,
						user=payment.user,
						payment=payment,
						value=value
					)
					vouchers.append(voucher)

				# Mark the user's basket items as redeemed
				payment.user.basket_items.update(is_redeemed=True)

				# Serialize the vouchers and return the response
				voucher_serializer = VoucherSerializer(vouchers, many=True)
				return Response(data={'message': 'Payment confirmed and vouchers created', 'vouchers': voucher_serializer.data}, status=status.HTTP_200_OK)
			except Payment.DoesNotExist:
				return Response(data={'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
		else:
			return Response(data={'error': 'Payment confirmation failed'}, status=status.HTTP_400_BAD_REQUEST)

	def generate_unique_voucher_code(self):
		# Generate a random voucher code and check for uniqueness
		while True:
			value = str(uuid.uuid4().hex)[:16]
			if not Voucher.objects.filter(value=value).exists():
				return value

	def verify_paypal_payment(self, payment_id):
		# Implement PayPal payment verification using 'paypalrestsdk' or other libraries
		# For example, you can call PayPal's API to verify the payment status
		# Here, we are assuming you have implemented this function
		# and it returns True for successful payments and False otherwise
		return True  # Replace this with the actual verification logic
