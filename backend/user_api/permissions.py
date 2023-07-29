from rest_framework.permissions import BasePermission
from .models import Merchant

class HasValidAPIKey(BasePermission):
    def has_permission(self, request, view):
        api_key = request.data.get('api_key', None)

        if not api_key:
            return False

        try:
            merchant = Merchant.objects.get(api_key=api_key)
        except Merchant.DoesNotExist:
            return False
        request.merchant_id = merchant.id

        return True
