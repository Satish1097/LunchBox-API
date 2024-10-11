from django.core.management.base import BaseCommand
from authapp.models import Order, MenuItem, OrderItem, Subscription


class Command(BaseCommand):
    def handle(self, *args, **options):
        subscription_users = Subscription.objects.filter(is_active=True).select_related(
            "child"
        )

        for subscription in subscription_users:
            child = subscription.child

            order = Order.objects.create(child=child)

            menu_item = MenuItem.objects.first()
            if menu_item:
                order_item = OrderItem.objects.create(order=order, menu_item=menu_item)

                self.stdout.write(
                    self.style.SUCCESS(f"Order Created for child: {child.Full_Name}")
                )
            else:
                self.stdout.write(self.style.ERROR("No Menu Items found"))

        self.stdout.write(self.style.SUCCESS("Order Creation Completed"))
