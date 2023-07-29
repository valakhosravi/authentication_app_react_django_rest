from rest_framework.response import Response
from django.utils import timezone
from ..permissions import HasValidAPIKey
from ..serializers import TransactionSerializer, VoucherBalanceRequestSerializer, VoucherRedeemRequestSerializer, VoucherSerializer
from ..models import Voucher
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions


class VoucherBalanceView(APIView):
    permission_classes = (permissions.AllowAny, HasValidAPIKey,)

    @swagger_auto_schema(request_body=VoucherBalanceRequestSerializer)
    def post(self, request):
        serializer = VoucherBalanceRequestSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            voucher_code = serializer.validated_data['voucher_code']
            try:
                voucher = Voucher.objects.get(code=voucher_code)
            except Voucher.DoesNotExist:
                return Response({'error': 'Voucher not found.'}, status=404)

            if voucher.expire_at is not None and voucher.expire_at < timezone.now():
                return Response({'error': 'Voucher has expired.'}, status=400)

            if voucher.is_used:
                return Response({'error': 'Voucher has already been used.'}, status=400)

            serializer = VoucherSerializer(voucher)
            return Response(serializer.data, status=200)

class VoucherRedeemView(APIView):
    permission_classes = (permissions.AllowAny, HasValidAPIKey,)

    @swagger_auto_schema(request_body=VoucherRedeemRequestSerializer)
    def post(self, request):
        serializer = VoucherRedeemRequestSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            voucher_code = serializer.validated_data['voucher_code']
            try:
                voucher = Voucher.objects.get(code=voucher_code)
            except Voucher.DoesNotExist:
                return Response({'error': 'Voucher not found.'}, status=404)

            if voucher.expire_at is not None and voucher.expire_at < timezone.now():
                return Response({'error': 'Voucher has expired.'}, status=400)

            if voucher.is_used:
                return Response({'error': 'Voucher has already been used.'}, status=400)

            if voucher.amount != serializer.validated_data['amount']:
                return Response({'error': 'Voucher amount and request amount should be equal.'}, status=400)

            merchant_id = request.merchant_id
            transaction_data = {
                'voucher': voucher.id,
                'merchant': merchant_id,
                'amount': voucher.amount
            }
            transaction_serializer = TransactionSerializer(data=transaction_data)
            if transaction_serializer.is_valid():
                transaction_serializer.save()
                voucher.is_used = True
                voucher.save()
                return Response({'message': 'Voucher redeemed successfully.'}, status=200)
            else:
                return Response(transaction_serializer.errors, status=400)
        
        return Response(serializer.errors, status=400)