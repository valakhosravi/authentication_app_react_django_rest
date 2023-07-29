from django.contrib import admin
from . import models

admin.site.register(models.AppUser)
admin.site.register(models.UserVerification)
admin.site.register(models.Currency)
admin.site.register(models.ExchangeRate)
class VoucherAdmin(admin.ModelAdmin):
    readonly_fields = ['create_at']
admin.site.register(models.Voucher, VoucherAdmin)

admin.site.register(models.Payment)
admin.site.register(models.Merchant)

class TransactionAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at']
admin.site.register(models.Transaction, TransactionAdmin)

