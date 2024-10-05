from rest_framework import generics, serializers
from rest_framework.response import Response
from rest_framework import status
import pyotp
from twilio.rest import Client
from .models import *
from rest_framework.generics import GenericAPIView
from .serializers import *
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import F


# Twilio credentials


class SendOTPView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        mobile_number = request.data.get("mobile_number")
        # Generate a new secret key and TOTP instance
        secret_key = pyotp.random_base32()  # Base32-encoded secret key
        totp = pyotp.TOTP(secret_key, interval=120)
        # Generate a 6-digit OTP
        otp = totp.now()

        # Send the OTP using Twilio
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"Your OTP is {otp}",
            from_="+1 775 235 0495",  # Twilio phone number bought using trial amount
            to=f"+91{mobile_number}",
        )

        # Save the secret key for verification later
        otp_record, _ = OTP.objects.get_or_create(mobile=mobile_number)
        otp_record.secret_key = secret_key
        otp_record.is_used = False
        otp_record.save()
        return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)


class VerifyOTPView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        mobile_number = request.data.get("mobile_number")
        user_otp = request.data.get("otp")

        try:
            otp_record = OTP.objects.get(mobile=mobile_number, is_used=False)
        except OTP.DoesNotExist:
            return Response(
                {"error": "OTP not found or already used"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if otp_record:
            print(f"User's OTP: {user_otp}")
            print(f"Stored Secret Key: {otp_record.secret_key}")

            totp = pyotp.TOTP(otp_record.secret_key, interval=120)

            if totp.verify(user_otp, valid_window=1):
                user, _ = User.objects.get_or_create(mobile=mobile_number)
                user.is_verified = True
                user.save()

                otp_record.is_used = True
                otp_record.save()

                # Create JWT token for the user
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                UserToken.objects.update_or_create(
                    user=user,
                    defaults={
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                )

                return Response(
                    {
                        "message": "OTP verified successfully",
                        "access_token": access_token,
                        "refresh_token": str(refresh),
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"message": "OTP verification failed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"error": "Invalid OTP provided"}, status=status.HTTP_400_BAD_REQUEST
            )


class UserPersonalDetailAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "mobile"

    def put(self, request, **kwargs):
        return self.update(request, **kwargs)

    def update(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)

        if serializer.is_valid():
            self.perform_update(serializer)
            instance.is_profile_completed = True
            instance.save()
            return Response({"success": "Details added successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save()


class RetrieveUserAPIView(GenericAPIView):
    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "mobile"

    def get(self, request, *args, **kwargs):
        mobile = kwargs.get("mobile")
        try:
            user = User.objects.get(mobile=mobile)
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                "User not found for this number", status=status.HTTP_404_NOT_FOUND
            )


class CreateChildAPIView(GenericAPIView):
    serializer_class = ChildSerializer

    def post(self, request):
        child_data = request.data
        serializer = self.serializer_class(data=child_data)

        if serializer.is_valid():
            # Save the child object and associate the parent (request.user)
            serializer.save(Parent=request.user)
            child = serializer.data
            return Response(
                {"data": child, "message": f"{child['Full_Name']} has been added"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        user = request.user
        childs = Child.objects.filter(Parent=user.id)
        serializer = self.get_serializer(childs, many=True)
        return Response(serializer.data)


class ListChildAPIView(GenericAPIView):
    queryset = Child.objects.all()
    serializer_class = ChildSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        childs = Child.objects.filter(Parent=user.id)
        serializer = self.get_serializer(childs, many=True)
        return Response(serializer.data)


class UpdateChildAPIView(GenericAPIView):
    queryset = Child.objects.all()
    serializer_class = ChildSerializer

    def put(self, request, **kwargs):
        return self.update(request, **kwargs)

    def update(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"success": "Details added successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        user = request.user
        instance = self.get_object()
        if instance.Parent == user:
            instance.delete()
            return Response(
                {"success": "Object deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response({"message": "Not Found"}, status=status.HTTP_400_BAD_REQUEST)


class ListCuisineAPIView(GenericAPIView):
    serializer_class = CuisineSerializer

    def get(self, request, *args, **kwargs):
        cuisines = Cuisine.objects.all()
        serializer = self.get_serializer(cuisines, many=True)
        return Response(serializer.data)


class AddCuisineAPIView(GenericAPIView):
    serializer_class = CuisineSerializer
    permission_classes = [IsAdminUser]

    def post(self, request):
        cuisine_data = request.data
        serializer = self.serializer_class(data=cuisine_data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"data": cuisine_data, "message": f"Cuisine has been added"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    queryset = Cuisine.objects.all()

    def delete(self, request, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"success": "Object deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )

    def perform_destroy(self, instance):
        instance.delete()


class ListMenuItemAPIView(GenericAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        print(pk)
        if pk:
            menuitems = MenuItem.objects.get(id=pk)
            serializer = self.get_serializer(menuitems)
            return Response(serializer.data)
        else:
            menuitems = MenuItem.objects.all()
            serializer = self.get_serializer(menuitems, many=True)
            return Response(serializer.data)


class MenuItemCreateView(GenericAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, **kwargs):
        return self.update(request, **kwargs)

    def update(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"success": "Details Updated successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"success": "Object deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class CreateRatingAPIView(GenericAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = RatingSerializer

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        menuitem = MenuItem.objects.get(id=pk)
        rating_data = request.data
        serializer = self.serializer_class(data=rating_data)

        if serializer.is_valid():
            try:
                rating = Rating.objects.get(user=request.user)
                if rating is not None:
                    return Response("You have already rated this product")
            except Rating.DoesNotExist:
                serializer.save(user=request.user, menu_item=menuitem)
                ratings = serializer.data
                return Response(
                    {"data": ratings, "message": f"rating added successfully"},
                    status=status.HTTP_201_CREATED,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        menuitem = MenuItem.objects.get(id=pk)
        ratings = Rating.objects.filter(menu_item=menuitem)
        serializer = self.serializer_class(ratings, many=True)
        return Response(serializer.data)


class AddtoCartAPIView(GenericAPIView):
    serializer_class = CartItemSerializer

    def post(self, request):
        cartitem_data = request.data
        serializer = self.serializer_class(data=cartitem_data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            Cart_Item = serializer.data
            return Response(
                {
                    "data": Cart_Item,
                    "message": "Cart_Item has been added",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        user = request.user
        cartitems = CartItem.objects.annotate(
            product_amount=F("product__price") * F("quantity")
        ).filter(user=request.user)
        serializer = self.get_serializer(cartitems, many=True)
        return Response(serializer.data)
