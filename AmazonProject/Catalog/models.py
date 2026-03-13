from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    current_progress = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Order(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),  # Hidden from user records until matched
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('frozen', 'Frozen'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.price and self.commission_rate:
            calc_profit = self.price * (self.commission_rate / Decimal('100'))
            self.profit = calc_profit.quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} ({self.user.username if self.user else 'Template'})"

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            Profile.objects.create(user=instance)