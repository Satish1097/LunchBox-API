from .models import *
from rest_framework import serializers
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken


class UserSerializer(serializers.ModelSerializer):
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["name", "email", "is_verified", "is_profile_completed"]


class SchoolAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolArea
        fields = "__all__"


class SchoolNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = "__all__"


class ChildSerializer(serializers.ModelSerializer):
    school_area = SchoolAreaSerializer(read_only=True, source="School_Area")
    school_name = SchoolNameSerializer(read_only=True, source="School_Name")

    school_name_id = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.all(), write_only=True, source="School_Name"
    )
    school_area_id = serializers.PrimaryKeyRelatedField(
        queryset=SchoolArea.objects.all(), write_only=True, source="School_Area"
    )

    class Meta:
        model = Child
        fields = [
            "id",
            "Full_Name",
            "Date_of_Birth",
            "Gender",
            "Class",
            "Division",
            "Notes",
            "Child_Image",
            "school_area",
            "school_name",
            "school_name_id",
            "school_area_id",
        ]

    def create(self, validated_data):
        # Pop the related fields to ensure they are passed to the model correctly
        school_name = validated_data.pop("School_Name")
        school_area = validated_data.pop("School_Area")
        # Create the child instance with the remaining validated data and the related fields
        child = Child.objects.create(
            School_Name=school_name, School_Area=school_area, **validated_data
        )
        return child


class UserChildSerializer(serializers.ModelSerializer):
    child = ChildSerializer(many=True, read_only=True)
    child_id = serializers.PrimaryKeyRelatedField(
        queryset=Child.objects.all(), many=True, write_only=True
    )

    class Meta:
        model = User
        fields = ["name", "email", "mobile", "child_id", "child"]


class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = ["id", "name"]


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"


class MenuItemSerializer(serializers.ModelSerializer):
    cuisine = CuisineSerializer(read_only=True)
    cuisine_id = serializers.PrimaryKeyRelatedField(
        queryset=Cuisine.objects.all(), write_only=True
    )

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "Item_Name",
            "Item_Image",
            "Item_Description",
            "Item_Price",
            "cuisine",
            "cuisine_id",
        ]

    def create(self, validated_data):
        cuisine = validated_data.pop("cuisine_id")
        return MenuItem.objects.create(cuisine=cuisine, **validated_data)


class CartItemSerializer(serializers.ModelSerializer):
    item_subtotal = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()  # Add unit price
    # For GET: Show the full menu item data
    menu_item = MenuItemSerializer(read_only=True)
    # child = ChildSerializer(read_only=True)
    # For POST: Accept the menu item ID and map it to the foreign key field 'menu_item'
    menu_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(), source="menu_item", write_only=True
    )
    child_id = serializers.PrimaryKeyRelatedField(
        queryset=Child.objects.all(), source="child", write_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            "id",
            "menu_id",  # For creating via POST (menu item ID)
            "menu_item",  # For retrieving via GET (full menu item object)
            "Item_Quantity",
            "unit_price",
            "item_subtotal",
            "child_id",
        ]
        extra_kwargs = {"menu_item": {"read_only": True}}

    def get_item_subtotal(self, obj):
        # Subtotal = quantity * unit price
        return obj.Item_Quantity * obj.menu_item.Item_Price

    def get_unit_price(self, obj):
        # Return the unit price of the menu item
        return obj.menu_item.Item_Price


class CartSerializer(serializers.Serializer):
    cart_items = CartItemSerializer(many=True)
    total_cart_price = serializers.SerializerMethodField()
    menu_item = MenuItemSerializer(read_only=True)

    menu_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(), source="menu_item", write_only=True
    )
    child_id = serializers.PrimaryKeyRelatedField(
        queryset=Child.objects.all(), source="child", write_only=True
    )

    def get_total_cart_price(self, obj):
        # Summing up subtotals of all cart items
        return sum(item.item_subtotal for item in obj["cart_items"])


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer()
    item_subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "Item_Quantity",
            "item_subtotal",
        ]

    def get_item_subtotal(self, obj):
        return obj.Item_Quantity * obj.menu_item.Item_Price


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    order_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "orderid",
            "child",
            "created_on",
            "order_status",
            "order_amount",
            "items",
        ]

    def get_order_amount(self, obj):
        return sum(item.item_subtotal for item in obj.items.all())


class PaymentSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    order_amount = serializers.IntegerField()


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(), write_only=True
    )

    class Meta:
        model = Subscription
        fields = ["child", "plan", "plan_id", "start_date", "end_date"]

        extra_kwargs = {
            "start_date": {"read_only": True},
            "end_date": {"read_only": True},
        }

    def create(self, validated_data):
        plan_id = validated_data.pop("plan_id")

        print(plan_id)
        subscription = Subscription.objects.create(plan=plan_id, **validated_data)
        return subscription


class TransactionDetailSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.all(), write_only=True
    )
    order = OrderSerializer(read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), write_only=True
    )

    class Meta:
        model = TransactionDetail
        fields = [
            "Transaction_id",
            "order",
            "order_id",
            "subscription_id",
            "subscription",
            "Payment_order_id",
            "payment_status",
            "child",
        ]


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate(self, attrs):
        # Ensure refresh token is provided
        if not attrs.get("refresh_token"):
            raise serializers.ValidationError("Refresh token is required.")
        return attrs

    def save(self):
        try:
            refresh_token = RefreshToken(self.validated_data["refresh_token"])

            # Check if the token is already blacklisted using check_blacklist()
            try:
                refresh_token.check_blacklist()  # Raises error if blacklisted
            except TokenError:
                raise serializers.ValidationError(
                    "The refresh token is already blacklisted."
                )

            # Blacklist the refresh token
            refresh_token.blacklist()

            # Attempt to blacklist the associated access token
            access_token = refresh_token.access_token

            # Blacklist associated access token explicitly
            jti = access_token.get("jti")  # Unique identifier for the token
            try:
                token = OutstandingToken.objects.get(jti=jti)
                token.blacklist()  # Mark access token as blacklisted
            except OutstandingToken.DoesNotExist:
                raise serializers.ValidationError("No associated access token found.")

            return {
                "detail": "Tokens successfully blacklisted."
            }  # Return success message
        except TokenError as e:
            raise serializers.ValidationError(f"Token error: {str(e)}")
        except Exception as e:
            raise serializers.ValidationError(f"Unexpected error: {str(e)}")


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = "__all__"


class DeliveryClusterSerializer(serializers.ModelSerializer):
    school = SchoolNameSerializer(read_only=True, many=True)
    Delivery_Agent = AgentSerializer(read_only=True)
    School_id = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.all(), many=True, write_only=True
    )
    Agent_id = serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.all(), write_only=True
    )

    class Meta:
        model = DeliveryCluster
        fields = [
            "id",
            "Cluster_Name",
            "Delivery_Agent",
            "School_id",
            "school",
            "Agent_id",
        ]

    def create(self, validated_data):
        # Extract school IDs from validated data
        school_ids = validated_data.pop("School_id")
        agent_id = validated_data.pop("Agent_id")
        # Create DeliveryCluster object
        delivery_cluster = DeliveryCluster.objects.create(
            Delivery_Agent=agent_id, **validated_data
        )
        # Add the schools by their IDs
        # schools = School.objects.filter(id__in=school_ids)
        delivery_cluster.school.set(school_ids)
        return delivery_cluster


class OrderMenuSerializer(serializers.Serializer):
    menu_item_name = serializers.CharField(source="menu_item__Item_Name")
    total_quantity = serializers.IntegerField()
