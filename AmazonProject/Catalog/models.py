from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

# ==========================================
# 1. PROFILE MODEL
# ==========================================

class Profile(models.Model):
    # Centralized Configuration - Adjust these values in one place
    VIP_CONFIG = {
        1: {'rate': Decimal('1.0'), 'limit': 40},
        2: {'rate': Decimal('1.4'), 'limit': 45},
        3: {'rate': Decimal('2.0'), 'limit': 50},
        4: {'rate': Decimal('2.8'), 'limit': 55},
        5: {'rate': Decimal('4.0'), 'limit': 60},
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    wallet_address = models.CharField(max_length=255, blank=True, null=True)
    network = models.CharField(max_length=50, default='ETH_USDC')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00')) 
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    current_progress = models.IntegerField(default=0)
    vip_level = models.IntegerField(default=1) 
    withdrawal_pin = models.CharField(max_length=6, default="000000")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Properties for easy access in Templates & Views ---

    @property
    def max_limit(self):
        """Usage: {{ profile.max_limit }}"""
        return self.VIP_CONFIG.get(self.vip_level, self.VIP_CONFIG[1])['limit']

    @property
    def current_rate(self):
        """Usage: profile.current_rate"""
        return self.VIP_CONFIG.get(self.vip_level, self.VIP_CONFIG[1])['rate']

    @property
    def is_at_limit(self):
        """Usage: {% if profile.is_at_limit %}"""
        return self.current_progress >= self.max_limit

    def __str__(self):
        return f"{self.user.username}'s Profile (VIP {self.vip_level})"


# ==========================================
# 2. ORDER MODEL
# ==========================================

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
    image_url = models.URLField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00')) 
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.50'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Auto-calculate profit based on commission rate: (Price * Rate) / 100
        # This ensures profit is always updated before saving to the database
        if self.price is not None and self.commission_rate is not None:
            self.profit = (self.price * self.commission_rate) / Decimal('100')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.product_name} ({self.status})"


# ==========================================
# 3. SIGNALS (USER -> PROFILE)
# ==========================================

@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    Automatically creates a Profile when a new User is created, 
    and ensures it exists when updating.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        # get_or_create is the safest way to ensure no RelatedObjectDoesNotExist errors
        # Note: We removed the extra .save() here to prevent unnecessary recursion
        Profile.objects.get_or_create(user=instance)