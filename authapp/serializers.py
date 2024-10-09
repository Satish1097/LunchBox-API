from .models import *
from rest_framework import serializers
from .models import SchoolArea, SchoolName
from django.db import transaction


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
        model = SchoolName
        fields = "__all__"


class ChildSerializer(serializers.ModelSerializer):
    school_area = SchoolAreaSerializer(read_only=True, source="School_Area")
    school_name = SchoolNameSerializer(read_only=True, source="School_Name")

    school_name_id = serializers.PrimaryKeyRelatedField(
        queryset=SchoolName.objects.all(), write_only=True, source="School_Name"
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


class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = "__all__"


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
            "payment_status",
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
