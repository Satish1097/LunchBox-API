from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import pyotp
from twilio.rest import Client
from .models import *
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
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
from dotenv import load_dotenv
import os
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.db.models import Sum

load_dotenv()


class SendOTPView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        mobile_number = request.data.get("mobile_number")
        # Generate a new secret key and Time based OTP instance
        secret_key = pyotp.random_base32()  # Base32-encoded secret key
        totp = pyotp.TOTP(secret_key, interval=120)
        # Generate a 6-digit OTP
        otp = totp.now()

        # Send the OTP using Twilio
        try:
            client = Client(os.getenv("account_sid"), os.getenv("auth_token"))
            message = client.messages.create(
                body=f"Your OTP is {otp}",
                from_=os.getenv(
                    "Twilio_Number"
                ),  # Twilio phone number bought using trial amount
                to=f"+91{mobile_number}",
            )
            # Save the secret key for verification later
            otp_record, _ = OTP.objects.get_or_create(mobile=mobile_number)
            otp_record.secret_key = secret_key
            otp_record.is_used = False
            otp_record.save()
            return Response(
                {"message": "OTP sent successfully"}, status=status.HTTP_200_OK
            )
        except:
            return Response("error")


class VerifyOTPView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
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
            totp = pyotp.TOTP(otp_record.secret_key, interval=120)

            if totp.verify(
                user_otp, valid_window=1
            ):  # valid window add 30 second before and after in actual time to validate the otp
                user, _ = User.objects.get_or_create(mobile=mobile_number)
                user.is_verified = True
                user.save()

                otp_record.is_used = True
                otp_record.save()

                # Create JWT token for the user
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

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
            serializer = self.get_serializer(instance)
            return Response(
                {"data": serializer.data, "message": "Record Updated"},
                status=status.HTTP_200_OK,
            )
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

        if pk and user.is_superuser:
            try:
                child = Child.objects.get(id=pk)
                serializer = self.get_serializer(child)
                return Response(serializer.data)
            except Child.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        elif pk:
            try:
                child = Child.objects.get(id=pk, Parent=user)
                serializer = self.get_serializer(child)
                return Response(serializer.data)
            except Child.DoesNotExist:
                return Response(
                    "Record does not exist", status=status.HTTP_404_NOT_FOUND
                )
        else:
            if user.is_superuser:
                children = Child.objects.all()
                serializer = self.get_serializer(children, many=True)
                return Response(serializer.data)
            else:
                children = Child.objects.filter(Parent=user.id)
                serializer = self.get_serializer(children, many=True)
                return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            if instance.Parent == request.user or request.user.is_superuser:
                serializer.save()
                return Response(
                    {"data": serializer.data, "success": "Details added successfully"}
                )
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        user = request.user
        instance = self.get_object()
        if instance.Parent == user or user.is_superuser:
            serializer = self.get_serializer(instance)
            instance.delete()
            return Response(
                {"data": serializer.data, "success": "Object deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response({"message": "Not Found"}, status=status.HTTP_400_BAD_REQUEST)


class CuisineAPIView(GenericAPIView):
    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                menuitems = Cuisine.objects.get(id=pk)
                serializer = self.get_serializer(menuitems)
                return Response(serializer.data)
            except Cuisine.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            menuitems = Cuisine.objects.all()
            serializer = self.get_serializer(menuitems, many=True)
            return Response(serializer.data)

    def post(self, request):
        cuisine_data = request.data
        cuisine = cuisine_data.get("name")
        try:
            cuisine_name = Cuisine.objects.get(name=cuisine)
            return Response("Cuisine With Same Name Already Exists")
        except Cuisine.DoesNotExist:
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

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "success": "Details Updated successfully"}
            )
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
                    {"data": ratings, "message": "rating added successfully"},
                    status=status.HTTP_201_CREATED,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        try:
            menuitem = MenuItem.objects.get(id=pk)
            ratings = Rating.objects.filter(menu_item=menuitem)
            serializer = self.serializer_class(ratings, many=True)
            return Response(serializer.data)
        except MenuItem.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        pk = self.kwargs.get("pk")
        user = request.user
        if pk and user:
            try:
                if user.is_superuser:
                    rating = Rating.objects.get(id=pk)
                    rating.delete()
                    return Response(
                        {"success": "Object deleted successfully"},
                        status=status.HTTP_204_NO_CONTENT,
                    )
                else:
                    rating = Rating.objects.get(user=user, id=pk)
                    rating.delete()
                    return Response(
                        {"success": "Object deleted successfully"},
                        status=status.HTTP_204_NO_CONTENT,
                    )
            except Rating.DoesNotExist:
                return Response(
                    {"Error": "Object Not Found"},
                    status=status.HTTP_400_BAD_REQUEST,
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
            return Response(
                {"data": serializer.data, "success": "Details Updated successfully"}
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        user = request.user
        instance = self.get_object()
        if instance.child.Parent == user:
            serializer = self.get_serializer(instance)
            instance.delete()
            return Response(
                {"data": serializer.data, "success": "Object deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response({"message": "Not Found"}, status=status.HTTP_400_BAD_REQUEST)


class OrderView(GenericAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get_permissions(self):
        if self.request.method == "PUT":
            return [IsAdminUser()]
        else:
            return [IsAuthenticated()]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                order = Order.objects.get(orderid=pk)
                serializer = self.get_serializer(order)
                return Response(serializer.data)
            except Order.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            child = request.data
            child_id = child.get("child_id")
            order_items = Order.objects.filter(child=child_id)
            serializer = self.get_serializer(order_items, many=True)
            return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        child = request.data
        child_id = child.get("child_id")
        try:
            child = Child.objects.get(id=child_id)
            cart_item = CartItem.objects.filter(child_id=child_id).exists()
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
                    return Response(
                        order_serializer.data, status=status.HTTP_201_CREATED
                    )
            else:
                return Response("Your Cart is Empty")
        except Child.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "success": "Details updated successfully"}
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
            try:
                plan = Plan.objects.get(id=pk)
                serializer = self.get_serializer(plan)
                return Response(serializer.data)
            except Plan.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
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
            return Response(
                {"data": serializer.data, "success": "Details updated successfully"}
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        instance = self.get_object()
        if instance:
            serializer = self.get_serializer(instance)
            instance.delete()
            return Response(
                {"data": serializer.data, "success": "Object deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response({"message": "Not Found"}, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionAPIView(GenericAPIView):
    serializer_class = SubscriptionSerializer
    queryset = Subscription.objects.all()

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")

        if pk:
            try:
                subscription = Subscription.objects.get(id=pk)
                serializer = self.get_serializer(subscription)
                return Response(serializer.data)
            except Subscription.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
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


class PaymentAPIView(GenericAPIView):
    def post(self, request, *args, **kwargs):

        # Get order_id, subscription_id, and order_amount from the request data
        order_id = request.data.get("order_id")
        subscription_id = request.data.get("subscription_id")
        order_amount = request.data.get("order_amount")
        order_amount = int(order_amount)
        client = razorpay.Client(auth=(os.getenv("key_id"), os.getenv("key_secret")))

        # Check whether it's an order payment or a subscription payment
        if order_id:
            try:
                order = Order.objects.get(orderid=order_id)
                amount = int(order_amount)
            except Order.DoesNotExist:
                return Response("Invalid OrderId", status=status.HTTP_400_BAD_REQUEST)
        elif subscription_id:
            try:
                subscription = Subscription.objects.get(id=subscription_id)
                amount = int(order_amount)
            except Subscription.DoesNotExist:
                return Response(
                    "Invalid Subscription Id", status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"error": "Either order_id or subscription_id must be provided"},
                status=400,
            )

        # Create Razorpay order
        payment = client.order.create(
            dict(
                amount=int(amount * 100),  # Amount in paise
                currency="INR",
                payment_capture="1",
            )
        )
        razorpay_order_id = payment["id"]
        # Create a TransactionDetail entry in the database
        if order_id:
            transaction = TransactionDetail.objects.create(
                order_id=order,
                transaction_amount=amount,
                Payment_order_id=razorpay_order_id,
                payment_status="Pending",
            )
        else:
            transaction = TransactionDetail.objects.create(
                subscription_id=subscription,
                transaction_amount=amount,
                Payment_order_id=razorpay_order_id,
                payment_status="Pending",
            )

        # Return the payment details
        return Response(
            {
                "razorpay_order_id": payment["id"],
                "order_id": order_id if order_id else None,
                "subscription_id": subscription_id if subscription_id else None,
                "transaction_id": transaction.Transaction_id,
                "amount": amount,
                "currency": "INR",
            }
        )


class PaymentHandlerView(GenericAPIView):
    @csrf_exempt
    def post(self, request):
        payment_id = request.data.get("razorpay_payment_id")
        order_id = request.data.get("razorpay_order_id")
        signature = request.data.get("razorpay_signature")
        amount = request.data.get(
            "amount"
        )  # Razorpay expects the amount in paise for capture
        amount = amount * 100
        if not payment_id or not order_id or not signature or not amount:
            return Response({"error": "Missing required fields"}, status=400)

        client = razorpay.Client(auth=(os.getenv("key_id"), os.getenv("key_secret")))

        # Step 1: Verify the payment signature
        params_dict = {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        }

        try:
            # Verifying signature
            client.utility.verify_payment_signature(params_dict)

            try:
                capture_response = client.payment.capture(payment_id, int(amount))
                # After capture update the payment_status in Transaction
                transaction = TransactionDetail.objects.get(payment_order_id=order_id)
                transaction.payment_status = "Done"
                transaction.save()

                return Response(
                    {
                        "status": "Payment successful",
                        "capture_response": capture_response,
                    },
                    status=status.HTTP_200_OK,
                )

            except Exception as capture_error:
                return Response(
                    {"error": "Payment capture failed", "details": str(capture_error)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except razorpay.errors.SignatureVerificationError:
            return Response(
                {"error": "Payment verification failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TransactionDetail.DoesNotExist:
            return Response(
                {"error": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": "An error occurred", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TransactionDetailAPIView(GenericAPIView):
    serializer_class = TransactionDetailSerializer
    queryset = TransactionDetail.objects.all()

    def get(self, request, *args, **kwargs):
        child_id = request.data.get("child_id")
        try:
            child = Child.objects.get(id=child_id)
            transaction = TransactionDetail.objects.filter(order_id__child=child)
            serializer = self.get_serializer(transaction, many=True)
            return Response(serializer.data)
        except Child.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            if (
                serializer.save()
            ):  # If save returns True, indicating successful access token expiration
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(
                    {"error": "Failed to expire access token"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Admin API's
class AdminLoginAPIView(GenericAPIView):
    pass


class SchoolNameAPIView(GenericAPIView):
    serializer_class = SchoolNameSerializer
    queryset = School.objects.all()
    permission_classes = [IsAdminUser]

    def get(self, request):
        schoolname = School.objects.all()
        serializer = self.get_serializer(schoolname, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "success": "Details Updated successfully"}
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"success": "Object deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class AgentAPIView(GenericAPIView):
    serializer_class = AgentSerializer
    queryset = Agent.objects.all()
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                agent = Agent.objects.get(id=pk)
                serializer = self.get_serializer(agent)
                return Response(serializer.data)
            except Agent.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            agents = Agent.objects.all()
            serializer = self.get_serializer(agents, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "success": "Details Updated successfully"}
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"success": "Object deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class ClusterAPIView(GenericAPIView):
    serializer_class = DeliveryClusterSerializer
    queryset = DeliveryCluster.objects.all()
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                cluster = DeliveryCluster.objects.get(id=pk)
                serializer = self.get_serializer(cluster)
                return Response(serializer.data)
            except DeliveryCluster.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            clusters = DeliveryCluster.objects.all()
            serializer = self.get_serializer(clusters, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        school_id = request.data.get("school_id")
        flag = request.data.get("flag")
        if school_id and flag == "remove":
            try:
                instance.school.remove(school_id)
            except Exception as e:
                return Response(
                    {"error": f"Failed to remove school with id {school_id}: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif school_id and flag == "add":
            try:
                instance.school.add(school_id)
            except Exception as e:
                return Response(
                    {"error": f"Failed to add school with id {school_id}: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "success": "Details updated successfully!"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        Agent_id = request.data.get("Agent_id")
        if Agent_id:
            try:
                agent = Agent.objects.get(id=Agent_id)
                instance.Delivery_Agent = agent
                instance.save()
            except Agent.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "success": "Details Updated successfully"}
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"success": "Object deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class OrderMenuDetailAPIView(GenericAPIView):
    queryset = Order.objects.all()
    permission_classes = [IsAdminUser]

    def get(self, request):
        # Get the current date and calculate yesterday's date
        current_date = timezone.now().date()
        yesterday = current_date - timedelta(days=1)

        # filter order related items before yesterday and equal to get all menuitem from them
        menu_summary = (
            OrderItem.objects.filter(order__created_on__date__gte=yesterday)
            .values("menu_item__Item_Name")  # Group by the MenuItem name
            .annotate(total_quantity=Sum("Item_Quantity"))  # Sum the quantities
        )
        serializer = OrderMenuSerializer(menu_summary, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserManagementAPIView(GenericAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get("pk")
        if pk:
            try:
                user = User.objects.prefetch_related("child").get(id=pk)
                serializer = UserChildSerializer(user)
                return Response(serializer.data)
            except User.DoesNotExist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            users = User.objects.prefetch_related("child")
            serializer = UserChildSerializer(users, many=True)
            return Response(serializer.data)

    # def put(self, request, *args, **kwargs):
    #     pk = self.kwargs.get("pk")
    #     try:
    #         user = User.objects.get(pk=pk)
    #         serializer = UserChildSerializer(user, data=request.data, partial=False)
    #         if serializer.is_valid():
    #             serializer.save()
    #             return Response(serializer.data)
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     except User.DoesNotExist:
    #         return Response(status=status.HTTP_400_BAD_REQUEST)

    # def patch(self, request, *args, **kwargs):
    #     pk = self.kwargs.get("pk")
    #     try:
    #         user = User.objects.prefetch_related("child").get(pk=pk)
    #         serializer = UserChildSerializer(user, data=request.data, partial=True)
    #         if serializer.is_valid():
    #             serializer.save()
    #             return Response(serializer.data)
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     except User.DoesNotExist:
    #         return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "success": "Details Updated successfully"}
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, **kwargs):
        instance = self.get_object()
        if instance:
            serializer = self.get_serializer(instance)
            instance.delete()
            return Response(
                {"data": serializer.data, "success": "Object deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response({"message": "Not Found"}, status=status.HTTP_400_BAD_REQUEST)
