from django.db import models
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator


class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Enter Valid Email Address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)

        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    mobile = models.CharField(max_length=13)
    is_verified = models.BooleanField(default=False)
    is_profile_completed = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    EMAIL_FILED = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name or self.email.split("@")[0]


class UserToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Token for {self.user.mobile}"


class Child(models.Model):
    Parent = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
    )
    Full_Name = models.CharField(max_length=256)
    Date_of_Birth = models.DateTimeField()
    Gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    School_Area = models.CharField(max_length=256)
    School_Name = models.CharField(max_length=256)
    Class = models.CharField(max_length=20)
    Division = models.CharField(max_length=10)
    Notes = models.CharField(max_length=1000, blank=True)
    Child_Image = models.ImageField(upload_to="ChildImage/", null=True)

    def __str__(self):
        return self.Full_Name


class OTP(models.Model):
    mobile = models.CharField(max_length=13, unique=True)
    secret_key = models.CharField(max_length=50)
    generated_at = models.DateTimeField(auto_now=True)
    is_used = models.BooleanField(default=False)

    # type-login/signup

    def __int__(self):
        return self.otp


class Cuisine(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    cuisine = models.ForeignKey(Cuisine, on_delete=models.CASCADE)
    Item_Image = models.ImageField(upload_to="MenuItem/")
    Item_Name = models.CharField(max_length=100)
    Item_Description = models.TextField()
    Item_Price = models.DecimalField(max_digits=8, decimal_places=2)

    def __int__(self):
        return self.id


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.CASCADE, related_name="ratings", null=True
    )
    ratings = models.PositiveIntegerField(
        validators=[MaxValueValidator(5), MinValueValidator(1)]
    )

    def __str__(self):
        return self.menu_item.Item_Name


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    Item_Quantity = models.PositiveBigIntegerField()

    def __str__(self):
        return self.user.mobile


class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.DO_NOTHING)
    Item_Quantity = models.PositiveBigIntegerField()

    def __str__(self):
        return f"Order for {self.user.mobile}"


class Plan(models.Model):
    PLAN_TYPE = (("MONTHLY", "Monthly"), ("WEEKLY", "Weekly"))
    Plan_Charges = models.DecimalField(max_digits=10, decimal_places=2)
    Plan_Description = models.TextField()
    Plan_Type = models.CharField(max_length=10, choices=PLAN_TYPE)

    def __str__(self):
        return self.Plan_Type
