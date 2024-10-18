from django.contrib import admin
from .models import User
from .models import *


class ChildAdmin(admin.ModelAdmin):
    list_display = (
        "Full_Name",
        "Date_of_Birth",
        "Gender",
        "Class",
        "Division",
        "get_parent_name",
        "get_school_name",
    )
    search_fields = ("Full_Name", "Class", "Division")
    list_filter = ("Gender", "School_Area", "School_Name")

    def get_school_name(self, obj):
        return obj.School_Name.schoolName if obj.School_Name else "No School"

    get_school_name.short_description = "School Name"

    # New method to retrieve parent's full name
    def get_parent_name(self, obj):
        return f"{obj.Parent.name}" if obj.Parent else "No Parent"

    get_parent_name.short_description = "Parent Name"  # Column header for parent's name


admin.site.register(Child, ChildAdmin)

admin.site.register(OTP)
admin.site.register(Cuisine)
admin.site.register(Rating)
admin.site.register(MenuItem)
admin.site.register(User)
# admin.site.register(Child)
admin.site.register(UserToken)
admin.site.register(CartItem)
admin.site.register(OrderItem)
admin.site.register(SchoolArea)
admin.site.register(School)
admin.site.register(Order)
admin.site.register(Plan)
admin.site.register(Subscription)
admin.site.register(TransactionDetail)
admin.site.register(Agent)
admin.site.register(DeliveryCluster)
