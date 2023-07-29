from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save

class AppUserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('An email is required.')
		if not password:
			raise ValueError('A password is required.')
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save()
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('An email is required.')
		if not password:
			raise ValueError('A password is required.')
		extra_fields.setdefault('is_superuser', True)
		extra_fields.setdefault('is_staff', True)
		return self.create_user(email, password, **extra_fields)

class AppUser(AbstractBaseUser, PermissionsMixin):
	id = models.AutoField(primary_key=True)
	first_name = models.CharField(max_length=50)
	last_name = models.CharField(max_length=50)
	Country = models.CharField(max_length=50, null=True, blank=True)
	City = models.CharField(max_length=50, null=True, blank=True)
	Gender = models.CharField(max_length=10, null=True, blank=True)
	Age = models.CharField(max_length=5, null=True, blank=True)
	phone_number = models.CharField(max_length=15, null=True, blank=True)
	zip_code = models.CharField(max_length=50, null=True, blank=True)
	email = models.EmailField(max_length=50, unique=True)
	password = models.CharField(max_length=128)
	is_staff = models.BooleanField(default=False)
	is_merchant = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	is_verified = models.BooleanField(default=False)
	create_at = models.DateTimeField(auto_now_add=True, editable=False)
	updated_at = models.DateTimeField(auto_now=True)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['first_name', 'last_name', 'password']

	objects = AppUserManager()

	def __str__(self):
		return self.email

class UserVerification(models.Model):
	id = models.AutoField(primary_key=True)
	user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
	code = models.CharField(max_length=20)
	create_at = models.DateTimeField(auto_now_add=True)
	expire_at = models.DateTimeField()

	def __str__(self):
		return f"Verification for {self.user.email}"

class Currency(models.Model):
	id = models.AutoField(primary_key=True)
	create_at = models.DateField(auto_now_add=True)
	name = models.CharField(max_length=100)
	symbol = models.CharField(max_length=10)

	def __str__(self):
		return self.name

class ExchangeRate(models.Model):
	id = models.AutoField(primary_key=True)
	create_at = models.DateField(auto_now_add=True)
	currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
	price = models.DecimalField(max_digits=20, decimal_places=2)

	def __str__(self):
		return f"{self.currency.name} - {self.price}"
		
User = get_user_model()

class Voucher(models.Model):
	id = models.AutoField(primary_key=True)
	amount = models.DecimalField(max_digits=20, decimal_places=2)
	purchased_by = models.ForeignKey(User, related_name='purchased_vouchers', on_delete=models.CASCADE)
	is_used = models.BooleanField(default=False)
	code = models.CharField(max_length=16, unique=True)
	purchased_for = models.CharField(max_length=50)
	create_at = models.DateTimeField(auto_now_add=True)
	expire_at = models.DateTimeField()

	def __str__(self):
		return f"Voucher ID: {self.id}, Amount: {self.amount}, Is used: {self.is_used}"
	
	def use_gift_card(self):
		if not self.is_used:
			self.is_used = True
			self.save()
			return True
		return False

class Payment(models.Model):
	id = models.AutoField(primary_key=True)
	create_at = models.DateTimeField(auto_now_add=True)
	create_by = models.ForeignKey(User, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=20, decimal_places=2)
	payment_method = models.CharField(max_length=50)
	vouchers = models.ForeignKey(Voucher, related_name='payment_vouchers', on_delete=models.CASCADE)
	value = models.CharField(max_length=16, unique=True)
	external_payment_id = models.CharField(max_length=50)
	is_successful = models.BooleanField(default=False)

	def __str__(self):
		return f"Payment ID: {self.id}, Amount: {self.amount}, Vouchers: {', '.join(str(voucher) for voucher in self.vouchers.all())}"
	
class Merchant(models.Model):
	id = models.AutoField(primary_key=True)
	number = models.CharField(max_length=10, unique=True)
	email = models.CharField(max_length=50, unique=True)
	name = models.CharField(max_length=100)
	description = models.TextField(blank=True)
	create_at = models.DateField(auto_now_add=True)
	updated_at = models.DateField(auto_now=True)
	api_key = models.CharField(max_length=100, unique=True)
	username = models.CharField(max_length=50, unique=True)
	password = models.CharField(max_length=100)

	def __str__(self):
		return f"{self.name} (ID: {self.id})"
		
@receiver(post_save, sender=Merchant)
def create_user_for_merchant(sender, instance, created, **kwargs):
	if created:
		User = get_user_model()
		user = User.objects.create_user(email=instance.username, password=instance.password,is_merchant=True)
		instance.user = user
		instance.save()
	
class Transaction(models.Model):
	id = models.AutoField(primary_key=True)
	created_at = models.DateTimeField(auto_now_add=True)
	amount = models.DecimalField(max_digits=20, decimal_places=2)
	voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
	merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)

	def __str__(self):
		return f"{self.id} ,Amount: {self.amount}"
	