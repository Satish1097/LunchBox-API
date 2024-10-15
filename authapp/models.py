from django.db import models
from django.contrib.auth.models import AbstractBaseUser, UserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
import uuid
from datetime import timedelta
import datetime


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


class SchoolArea(models.Model):
    area = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.area


class SchoolName(models.Model):
    schoolName = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.schoolName


class Child(models.Model):
    Parent = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
    )
    Full_Name = models.CharField(max_length=256)
    Date_of_Birth = models.DateTimeField()
    Gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    School_Area = models.ForeignKey(SchoolArea, on_delete=models.CASCADE)
    School_Name = models.ForeignKey(SchoolName, on_delete=models.CASCADE)
    Class = models.CharField(max_length=20)
    Division = models.CharField(max_length=10)
    Notes = models.CharField(max_length=1000, blank=True)
    Child_Image = models.ImageField(upload_to="ChildImage/", null=True)

    def __str__(self):
        return f"{self.Full_Name} - {self.id}"


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
    child = models.ForeignKey(Child, on_delete=models.CASCADE, null=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    Item_Quantity = models.PositiveBigIntegerField()

    def __str__(self):
        return self.child.Full_Name

    @property
    def item_subtotal(self):
        # Subtotal = quantity * price
        return self.Item_Quantity * self.menu_item.Item_Price


class Order(models.Model):
    Status_Choice = (
        ("Pending", "Pending"),
        ("Processing", "Processing"),
        ("Out For Delivery", "Out For Delivery"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    )
    orderid = models.CharField(
        max_length=100, default=uuid.uuid4, editable=False, primary_key=True
    )
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(
        max_length=20, choices=Status_Choice, default="Pending"
    )

    def __str__(self):
        return f"Order for {self.child.Full_Name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.DO_NOTHING)
    Item_Quantity = models.PositiveBigIntegerField(default=1)

    def __str__(self):
        return self.order.child.Full_Name

    @property
    def item_subtotal(self):
        # Subtotal = quantity * price
        return self.Item_Quantity * self.menu_item.Item_Price


class Plan(models.Model):
    PLAN_TYPE = (("Monthly", "Monthly"), ("Weekly", "Weekly"))
    Plan_Charges = models.DecimalField(max_digits=10, decimal_places=2)
    Plan_Description = models.TextField()
    Plan_Type = models.CharField(max_length=10, choices=PLAN_TYPE)

    def __str__(self):
        return f"{self.Plan_Type} - {self.id}"


class Subscription(models.Model):
    child = models.ForeignKey(
        Child, on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Set the start date 1 day next to subscription
        if not self.start_date:
            self.start_date = timezone.now() + timedelta(days=1)  # Starts from tomorrow

        # End date is calculated based on start date and sunday is also excluded
        if not self.end_date:
            if self.plan.Plan_Type == "Monthly":
                # Calculate the end date excluding Sundays for 30 active days
                self.end_date = self.calculate_end_date_excluding_sundays(
                    self.start_date, 30
                )
            else:
                # Weekly plan, just add 7 days
                self.end_date = self.start_date + timedelta(days=7)

        # Save the instance
        super(Subscription, self).save(*args, **kwargs)

    def calculate_end_date_excluding_sundays(self, start_date, active_days_needed):
        current_date = start_date
        active_days = 0

        # Loop through each day, skipping Sundays, until the required active days are counted
        while active_days < active_days_needed:
            if (
                current_date.weekday() != 6
            ):  # 6 represents Sunday day starts from monday that is 0.
                active_days += 1
            current_date += timedelta(days=1)
        return current_date

    def __str__(self):
        return f"{self.child.Full_Name} - {self.plan.Plan_Type} Subscription"


class TransactionDetail(models.Model):
    Status_Choices = (
        ("Done", "Done"),
        ("Failed", "Failed"),
        ("Pending", "Pending"),
    )
    order_id = models.ForeignKey(
        Order, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    subscription_id = models.ForeignKey(
        Subscription, on_delete=models.DO_NOTHING, blank=True, null=True
    )
    Transaction_id = models.CharField(
        max_length=100, default=uuid.uuid4, editable=False, primary_key=True
    )
    Payment_order_id = models.CharField(max_length=100, unique=True, null=True)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=3)
    payment_status = models.CharField(
        max_length=10, choices=Status_Choices, default="Pending"
    )
    child = models.ForeignKey(Child, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"{self.child.Full_Name} Transaction_id {self.Transaction_id}"
