from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authapp.models import Order, Subscription


class Command(BaseCommand):
    def handle(self, *args, **options):
        current_date = timezone.now().date()

        active_subscriptions = Subscription.objects.filter(is_active=True)

        for subscription in active_subscriptions:
            child = subscription.child

            cancelled_orders = Order.objects.filter(
                child=child,
                order_status="Cancelled",
                created_on__gte=subscription.start_date,
                created_on__date=current_date,
            ).exists()
            if cancelled_orders:
                new_end_date = subscription.end_date + timedelta(days=1)
                self.stdout.write(self.style.SUCCESS({new_end_date}))

                if new_end_date > subscription.end_date:
                    subscription.end_date = new_end_date
                    subscription.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Subscription for {child.Full_Name} extended by {1} day(s) due to {1} unique canceled order(s)."
                        )
                    )
            elif subscription.end_date.date() == timezone.now().date():
                subscription.is_active = False
                subscription.save()
                self.stdout.write(
                    self.style.WARNING(
                        f"No new canceled orders to process for {child.Full_Name}."
                    )
                )

        self.stdout.write(self.style.SUCCESS("Cancelled orders check completed."))
