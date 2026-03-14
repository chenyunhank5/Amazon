from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Increased max_digits
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    current_progress = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Order(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('frozen', 'Frozen'),
        ('withdrawal', 'Withdrawal Pending'), 
        ('withdrawn', 'Withdrawn/Paid'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) 
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # FIX: Ensure everything is cast to Decimal to prevent "float / Decimal" error
        if self.price is not None and self.commission_rate is not None:
            price_dec = Decimal(str(self.price))
            comm_dec = Decimal(str(self.commission_rate))
            self.profit = (price_dec * comm_dec) / Decimal('100')
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} ({self.user.username if self.user else 'Template'})"

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        # Use get_or_create to be safer
        Profile.objects.get_or_create(user=instance)
        instance.profile.save()