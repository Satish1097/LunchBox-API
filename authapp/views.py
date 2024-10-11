from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
import pyotp
from twilio.rest import Client
from .models import *
from rest_framework.generics import GenericAPIView
from .serializers import *
from django.shortcuts import get_object_or_404
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    IsAuthenticatedOrReadOnly,
)
from rest_framework_simplejwt.tokens import RefreshToken
import razorpay




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
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "mobile"

    def put(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            instance.is_profile_completed = True
            instance.save()
            return Response({"success": "Details added successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RetrieveUserAPIView(GenericAPIView):
    permission_classes = [IsAuthenticated]
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


class ChildAPIView(GenericAPIView):
    serializer_class = ChildSerializer
    queryset = Child.objects.all()

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(Parent=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        user = request.user
        if pk and user is not None:
            child = Child.objects.get(id=pk)
            serializer = self.get_serializer(child)
            return Response(serializer.data)
        else:
            children = Child.objects.filter(Parent=user.id)
            serializer = self.get_serializer(children, many=True)
            return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            if instance.Parent == request.user:
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


class CuisineAPIView(GenericAPIView):
    serializer_class = CuisineSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]

    def get(self, request, *args, **kwargs):
        cuisines = Cuisine.objects.all()
        serializer = self.get_serializer(cuisines, many=True)
        return Response(serializer.data)

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

    def delete(self, request, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"success": "Object deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )

    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                menuitems = MenuItem.objects.get(id=pk)
                serializer = self.get_serializer(menuitems)
                return Response(serializer.data)
            except MenuItem.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            menuitems = MenuItem.objects.all()
            serializer = self.get_serializer(menuitems, many=True)
            return Response(serializer.data)


class MenuItemAPIView(GenericAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                menuitems = MenuItem.objects.get(id=pk)
                serializer = self.get_serializer(menuitems)
                return Response(serializer.data)
            except MenuItem.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            menuitems = MenuItem.objects.all()
            serializer = self.get_serializer(menuitems, many=True)
            return Response(serializer.data)

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


class RatingAPIView(GenericAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = RatingSerializer

    def post(self, request, *args, **kwargs):
        rating_data = request.data
        menu_id = rating_data["menu_id"]
        serializer = self.serializer_class(data=rating_data)

        if serializer.is_valid():
            try:
                rating = Rating.objects.get(user=request.user, menu_item_id=menu_id)
                if rating is not None:
                    return Response("You have already rated this product")
            except Rating.DoesNotExist:
                serializer.save(user=request.user, menu_item_id=menu_id)
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

    def delete(self, request, **kwargs):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                rating = Rating.objects.get(id=pk)
                rating.delete()
                return Response(
                    {"success": "Object deleted successfully"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            except Rating.DoesNotExist:
                return Response(
                    {"Error": "Object Not Found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(status=status.HTTP_404_NOT_FOUND)


class CartAPIView(GenericAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def post(self, request):
        cartitem_data = request.data
        menu_id = cartitem_data.get("menu_id")
        child = cartitem_data.get("child_id")
        serializer = self.serializer_class(data=cartitem_data)
        if serializer.is_valid():
            try:
                cartitem = CartItem.objects.get(menu_item=menu_id, child=child)
                if cartitem:
                    return Response("Items already in Cart")
            except CartItem.DoesNotExist:
                serializer.save()
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
        child_id = request.data.get("child_id")
        pk = self.kwargs.get("pk")
        if pk is None:
            # Get all cart items for the authenticated user
            if child_id is not None:
                cart_items = CartItem.objects.filter(child=child_id)
                cart_data = {"cart_items": cart_items}
                # Serialize the cart
                serializer = CartSerializer(cart_data)
                return Response(serializer.data)
            else:
                childs = Child.objects.filter(Parent=request.user).values_list(
                    "id", flat=True
                )
                cart_items = CartItem.objects.filter(child_id__in=childs)

                cart_data = {"cart_items": cart_items}
                # Serialize the cart
                serializer = CartSerializer(cart_data)
                return Response(serializer.data)
        else:
            try:
                cart_item = CartItem.objects.get(id=pk)
                serializer = self.serializer_class(cart_item)
                return Response(serializer.data)
            except CartItem.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"success": "Details Updated successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        user = request.user
        instance = self.get_object()
        if instance.child.Parent == user:
            instance.delete()
            return Response(
                {"success": "Object deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response({"message": "Not Found"}, status=status.HTTP_400_BAD_REQUEST)


class OrderView(GenericAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        if pk:
            order = Order.objects.get(orderid=pk)
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        else:
            child = request.data
            child_id = child.get("child_id")
            order_items = Order.objects.filter(child=child_id)
            serializer = self.get_serializer(order_items, many=True)
            return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        child = request.data
        child_id = child.get("child_id")
        child = Child.objects.get(id=child_id)
        print(child_id)
        cart_item = CartItem.objects.filter(child_id=child_id).exists()
        print(cart_item)
        if cart_item is True:
            with transaction.atomic():
                order = Order.objects.create(child=child)
                cartitems = CartItem.objects.filter(child_id=child_id)
                for item in cartitems:
                    OrderItem.objects.create(
                        order=order,
                        menu_item=item.menu_item,
                        Item_Quantity=item.Item_Quantity,
                    )
                    item.delete()
                order_serializer = OrderSerializer(order)
                return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response("Your Cart is Empty")

    def put(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"success": "Details Updated successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentAPIView(GenericAPIView):
    serializer_class = PaymentSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        order_amount = serializer.validated_data["order_amount"]
        order = Order.objects.get(orderid=order_id)

        amount = order_amount
        currency = "INR"
        client = razorpay.Client(
        )
        payment = client.order.create(
            dict(
                amount=amount * 100,  # Amount in paise
                currency=currency,
                payment_capture="1",
            )
        )
        return Response("payment_Done")


class PlanAPIView(GenericAPIView):
    serializer_class = PlanSerializer
    queryset = Plan.objects.all()

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        if pk is not None:
            plan = Plan.objects.get(id=pk)
            serializer = self.get_serializer(plan)
            return Response(serializer.data)
        else:
            plans = Plan.objects.all()
            serializer = self.get_serializer(plans, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"success": "Details updated successfully"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        instance = self.get_object()
        if instance:
            instance.delete()
            return Response(
                {"success": "Object deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response({"message": "Not Found"}, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionAPIView(GenericAPIView):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")

        if pk:
            subscription = Subscription.objects.get(id=pk)
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        else:
            child_id = request.data.get("child_id")
            subscriptions = Subscription.objects.filter(
                child__Parent=request.user, child=child_id
            )
            serializer = self.get_serializer(subscriptions, many=True)
            return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            child = serializer.validated_data.get("child")
            if child.Parent == request.user:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    "Invalid Child data", status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
