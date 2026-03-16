import random
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth import login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Case, When, Value, IntegerField
from django.db import transaction
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Profile, Order
from .forms import UserRegistrationForm, CleanLoginForm

# ==========================================
# 1. GENERAL & AUTHENTICATION
# ==========================================

@login_required(login_url='user_login')
def home(request):
    profile = request.user.profile
    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    all_completed = Order.objects.filter(user=request.user, status='completed')
    earned_today = all_completed.filter(created_at__date=today).aggregate(Sum('profit'))['profit__sum'] or 0
    earned_yesterday = all_completed.filter(created_at__date=yesterday).aggregate(Sum('profit'))['profit__sum'] or 0
    earned_this_month = all_completed.filter(created_at__gte=start_of_month).aggregate(Sum('profit'))['profit__sum'] or 0

    return render(request, 'users/home.html', {
        'profile': profile,
        'earned_today': earned_today,
        'earned_yesterday': earned_yesterday,
        'earned_this_month': earned_this_month
    })

def staff_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                return redirect('staffs')
            else:
                messages.error(request, "Access denied. Staff only.")
    else:
        form = AuthenticationForm()
    return render(request, 'staffs/staffs_login.html', {'form': form})

def staff_logout(request):
    logout(request)
    return redirect('staff_login')

def user_login(request):
    if request.method == 'POST':
        form = CleanLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('user_dashboard')
    else:
        form = CleanLoginForm()
    return render(request, 'users/user_login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('user_login')

def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # The form.clean_phone_number() now handles the UNIQUE check
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data.get('password'))
                user.save()
                
                # Get or Create profile to avoid 'RelatedObjectDoesNotExist'
                profile, created = Profile.objects.get_or_create(user=user)
                profile.phone_number = form.cleaned_data.get('phone_number')
                # Optional: set a default pin if your form doesn't have it yet
                if 'withdrawal_pin' in form.cleaned_data:
                    profile.withdrawal_pin = form.cleaned_data.get('withdrawal_pin')
                profile.save()
                
            messages.success(request, 'Account created! Please log in.')
            return redirect('user_login')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/user_register.html', {'form': form})

# ==========================================
# 2. STAFF DASHBOARD
# ==========================================

@staff_member_required(login_url='staff_login')
def staffs(request):
    u_search = request.GET.get('search', '')
    t_search = request.GET.get('template_search', '')
    w_search = request.GET.get('withdrawal_search', '')
    o_search = request.GET.get('order_search', '')
    
    u_page_num = request.GET.get('page', 1)
    t_page_num = request.GET.get('t_page', 1)
    w_page_num = request.GET.get('withdrawal_page', 1)
    o_page_num = request.GET.get('log_page', 1)

    user_list = User.objects.filter(is_staff=False, is_superuser=False).select_related('profile').order_by('-id')
    if u_search:
        user_list = user_list.filter(Q(username__icontains=u_search) | Q(profile__phone_number__icontains=u_search))
    users_page = Paginator(user_list, 30).get_page(u_page_num)

    template_list = Order.objects.filter(user__isnull=True).order_by('-created_at')
    if t_search:
        template_list = template_list.filter(product_name__icontains=t_search)
    templates_page = Paginator(template_list, 10).get_page(t_page_num)

    withdrawal_list = Order.objects.filter(
        status__in=['withdrawal', 'withdrawn', 'rejected']
    ).select_related('user', 'user__profile').order_by('-created_at')
    
    if w_search:
        withdrawal_list = withdrawal_list.filter(
            Q(user__username__icontains=w_search) | 
            Q(user__profile__phone_number__icontains=w_search)
        )
    withdrawals_page = Paginator(withdrawal_list, 20).get_page(w_page_num)

    log_list = Order.objects.filter(user__isnull=False).exclude(
        status__in=['withdrawal', 'withdrawn', 'rejected', 'scheduled']
    ).select_related('user', 'user__profile').order_by('-created_at')
    
    if o_search:
        log_list = log_list.filter(
            Q(user__username__icontains=o_search) | 
            Q(user__profile__phone_number__icontains=o_search) |
            Q(product_name__icontains=o_search)
        )
    
    total_profit_val = log_list.filter(status='completed').aggregate(Sum('profit'))['profit__sum'] or 0
    total_profit = Decimal(str(total_profit_val)).quantize(Decimal('0.01'))
    
    logs_page = Paginator(log_list, 30).get_page(o_page_num)

    return render(request, 'staffs/staffs_main.html', {
        'users': users_page,
        'task_templates': templates_page,
        'withdrawal_logs': withdrawals_page,
        'withdrawals_page': withdrawals_page,
        'user_logs': logs_page,
        'total_profit': total_profit,
        'search_query': u_search,
        'template_search_query': t_search,
        'withdrawal_search_query': w_search,
        'order_search_query': o_search,
        'active_tab': request.GET.get('tab', 'users'),
    })

@staff_member_required(login_url='staff_login')
def delete_order_record(request, order_id):
    order = get_object_or_404(Order, id=order_id, user__isnull=False)
    order.delete()
    messages.success(request, "Order record deleted successfully.")
    return redirect(f"{reverse('staffs')}?tab=records")

# ==========================================
# 3. STAFF: USER MANAGEMENT
# ==========================================

@staff_member_required(login_url='staff_login')
def adjust_balance(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        profile = user.profile
        try:
            amount = Decimal(request.POST.get('amount', '0'))
            with transaction.atomic():
                profile.balance += amount
                profile.save()
            messages.success(request, f"Updated balance for {user.username} by ${amount}")
        except (InvalidOperation, ValueError):
            messages.error(request, "Invalid amount entered.")
    return redirect(f"{reverse('staffs')}?tab=users")

@staff_member_required(login_url='staff_login')
def add_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.phone_number = form.cleaned_data.get('phone_number')
            profile.save()
            messages.success(request, f"User {user.username} created.")
            return redirect('staffs')
    else:
        form = UserRegistrationForm()
    return render(request, 'staffs/add_user.html', {'form': form})

@staff_member_required(login_url='staff_login')
def edit_user(request, user_id):
    user_to_edit = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=user_to_edit)
    password_form = SetPasswordForm(user_to_edit)

    if request.method == 'POST':
        if 'update_info' in request.POST:
            user_to_edit.username = request.POST.get('username')
            user_to_edit.save()
            profile.current_progress = int(request.POST.get('current_progress', 0))
            profile.phone_number = request.POST.get('phone', '')
            profile.withdrawal_pin = request.POST.get('withdrawal_pin', '000000')
            profile.save()
            messages.success(request, "Profile updated successfully!")
        
        elif 'update_wallet' in request.POST:
            profile.wallet_address = request.POST.get('wallet_address', '')
            profile.network = request.POST.get('network', 'ETH_USDC')
            profile.save()
            messages.success(request, "Wallet and network updated!")
            
        elif 'update_password' in request.POST:
            password_form = SetPasswordForm(user_to_edit, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Password reset successfully!")
        
        return redirect('edit_user', user_id=user_id)

    return render(request, 'staffs/edit_user.html', {
        'user_to_edit': user_to_edit, 
        'password_form': password_form
    })

@staff_member_required(login_url='staff_login')
def delete_user(request, user_id):
    get_object_or_404(User, id=user_id).delete()
    return redirect('staffs')

@staff_member_required(login_url='staff_login')
def reset_user_orders(request, user_id):
    user_to_reset = get_object_or_404(User, id=user_id)
    profile = user_to_reset.profile
    profile.current_progress = 0
    profile.save()
    messages.success(request, f"Progress for {user_to_reset.username} reset to 0.")
    return redirect('staffs')

@staff_member_required(login_url='staff_login')
def add_order_staff(request):
    if request.method == 'POST':
        try:
            Order.objects.create(
                product_name=request.POST.get('product_name', '').strip(),
                price=Decimal(request.POST.get('price', '0').strip()),
                commission_rate=Decimal(request.POST.get('commission_rate', '0').strip()),
                image_url=request.POST.get('image_url', '').strip()
            )
            messages.success(request, "Order template created.")
            return redirect('staffs')

        except (InvalidOperation, ValueError):
            messages.error(request, "Invalid price or commission rate.")
            return redirect('staffs')

    return render(request, 'staffs/add_order.html')


@staff_member_required(login_url='staff_login')
def edit_order_staff(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        try:
            order.product_name = request.POST.get('product_name', '').strip()
            order.image_url = request.POST.get('image_url', '').strip()
            order.price = Decimal(request.POST.get('price', '0').strip())
            order.commission_rate = Decimal(request.POST.get('commission_rate', '0').strip())
            order.save()

            messages.success(request, "Order template updated.")
            return redirect('staffs')

        except (InvalidOperation, ValueError):
            messages.error(request, "Invalid price or commission rate.")

    return render(request, 'staffs/edit_order.html', {'order': order})

@staff_member_required(login_url='staff_login')
def delete_order_staff(request, order_id):
    get_object_or_404(Order, id=order_id).delete()
    return redirect('staffs')

@staff_member_required(login_url='staff_login')
def manual_assign_order(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    templates = Order.objects.filter(user__isnull=True).order_by('price')
    scheduled_orders = target_user.orders.filter(status='scheduled').order_by('scheduled_at')

    if request.method == 'POST':
        if 'delete_scheduled' in request.POST:
            get_object_or_404(Order, id=request.POST.get('order_id'), user=target_user).delete()
        else:
            template = get_object_or_404(Order, id=request.POST.get('template_id'))
            Order.objects.create(
                user=target_user,
                product_name=template.product_name,
                price=template.price,
                commission_rate=template.commission_rate,
                status='scheduled',
                scheduled_at=int(request.POST.get('target_num', 0)),
                image_url=template.image_url 
            )
        return redirect('manual_assign_order', user_id=user_id)
    return render(request, 'staffs/manual_assign.html', {'target_user': target_user, 'templates': templates, 'scheduled_orders': scheduled_orders})

# ==========================================
# 4. WALLET MANAGEMENT
# ==========================================

@login_required(login_url='user_login')
def edit_wallet(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.wallet_address = request.POST.get('wallet_address', '').strip()
        profile.network = request.POST.get('network')
        profile.save()
        messages.success(request, "Wallet and network preferences saved!")
        return redirect('user_settings')
        
    return render(request, 'users/edit_wallet.html', {'profile': profile})

@login_required(login_url='user_login')
def update_wallet_address(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.wallet_address = request.POST.get('wallet_address')
        profile.save()
        messages.success(request, "Wallet address updated successfully!")
    return redirect('user_wallet')

# ==========================================
# 5. USER PORTAL & MATCHING
# ==========================================

@login_required(login_url='user_login')
def user_dashboard(request):
    return render(request, 'users/home.html', {'profile': request.user.profile})

@login_required(login_url='user_login')
def user_order(request):
    orders = request.user.orders.exclude(status__in=['scheduled', 'withdrawal', 'withdrawn']).order_by('-created_at')
    return render(request, 'users/order.html', {
        'profile': request.user.profile, 
        'orders': orders, 
        'order_count': request.user.profile.current_progress, 
        'max_orders': 40
    })

@login_required(login_url='user_login')
def user_record(request):
    status_filter = request.GET.get('status')
    orders = request.user.orders.exclude(
        status__in=['scheduled', 'withdrawal', 'withdrawn', 'rejected']
    ).annotate(
        priority=Case(
            When(status='pending', then=Value(1)),
            When(status='completed', then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
    ).order_by('priority', '-created_at')

    if status_filter in ['pending', 'completed']:
        orders = orders.filter(status=status_filter)
    
    paginator = Paginator(orders, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'users/record.html', {
        'profile': request.user.profile, 
        'orders': page_obj, 
        'current_status': status_filter
    })

@login_required(login_url='user_login')
def start_matching(request):
    profile = request.user.profile
    if profile.current_progress >= 40:
        messages.error(request, "Daily limit reached.")
        return redirect('user_order')

    current_num = profile.current_progress + 1
    trap = request.user.orders.filter(status='scheduled', scheduled_at=current_num).first()
    
    if trap:
        trap.status = 'pending'
        trap.save()
        return render(request, 'users/confirm_order.html', {'order': trap, 'profile': profile})

    pending = request.user.orders.filter(status='pending').first()
    if pending:
        return render(request, 'users/confirm_order.html', {'order': pending, 'profile': profile})

    if profile.balance < 10:
        messages.error(request, "Minimum $10 required.")
        return redirect('user_order')

    templates = Order.objects.filter(user__isnull=True, price__lte=profile.balance)
    if not templates.exists():
        messages.error(request, "No suitable tasks found.")
        return redirect('user_order')

    temp = random.choice(templates)
    order = Order.objects.create(
        user=request.user, product_name=temp.product_name,
        price=temp.price, commission_rate=temp.commission_rate, 
        status='pending',
        image_url=temp.image_url 
    )
    return render(request, 'users/confirm_order.html', {'order': order, 'profile': profile})

@login_required(login_url='user_login')
def complete_order(request, order_id):
    if request.method == 'POST':
        with transaction.atomic():
            order = get_object_or_404(Order.objects.select_for_update(), id=order_id, user=request.user)
            profile = request.user.profile
            if order.status == 'completed': 
                return redirect('user_order')
            if profile.balance < order.price:
                messages.error(request, "Insufficient funds.")
                return redirect(f"{reverse('user_record')}?status=pending")

            profile.balance += order.profit 
            profile.total_earned += order.profit 
            order.status = 'completed'
            order.save()
            profile.current_progress += 1
            profile.save()
            messages.success(request, f"Profit: ${order.profit}")
            return redirect('user_order')
    return redirect('user_record')

# ==========================================
# 6. WALLET & CRYPTO WITHDRAWAL
# ==========================================

@login_required(login_url='user_login')
def user_wallet(request):
    withdrawal_orders = request.user.orders.filter(
        status__in=['withdrawal', 'withdrawn', 'rejected']
    ).order_by('-created_at')
    
    paginator = Paginator(withdrawal_orders, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'users/wallet.html', {
        'profile': request.user.profile,
        'withdrawals': page_obj
    })

@login_required(login_url='user_login')
def withdraw_funds(request):
    profile = request.user.profile
    if request.method == 'POST':
        pin = request.POST.get('pin', '') 
        try:
            amount = Decimal(request.POST.get('amount', '0'))
        except (InvalidOperation, ValueError):
            amount = Decimal('0')

        if pin != profile.withdrawal_pin:
            messages.error(request, "Incorrect 6-digit PIN.")
        elif amount < Decimal('10.00'):
            messages.error(request, "Minimum withdrawal is $10.00")
        elif amount > profile.balance:
            messages.error(request, "Insufficient balance.")
        elif not profile.wallet_address:
            messages.error(request, "Wallet address is required.")
        else:
            with transaction.atomic():
                profile.balance -= amount
                profile.save()
                Order.objects.create(
                    user=request.user,
                    product_name=f"Withdrawal ({profile.network}) to {profile.wallet_address}",
                    price=amount, 
                    status='withdrawal'
                )
            messages.success(request, "Withdrawal request submitted.")
            return redirect('withdraw_funds')
    
    withdrawals = Order.objects.filter(
        user=request.user, 
        status__in=['withdrawal', 'withdrawn']
    ).order_by('-created_at')
    
    paginator = Paginator(withdrawals, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'users/withdrawal.html', {
        'profile': profile,
        'withdrawals': page_obj
    })

@login_required(login_url='user_login')
def security_settings(request):
    profile = request.user.profile
    password_form = PasswordChangeForm(request.user)

    if request.method == 'POST':
        if 'update_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user) 
                messages.success(request, "Login password updated successfully!")
                return redirect('security_settings')
            else:
                messages.error(request, "Error updating password.")

        elif 'update_pin' in request.POST:
            old_pin = request.POST.get('old_pin')
            new_pin = request.POST.get('new_pin')
            confirm_pin = request.POST.get('confirm_pin')

            if old_pin != profile.withdrawal_pin:
                messages.error(request, "Current Withdrawal PIN is incorrect.")
            elif new_pin != confirm_pin:
                messages.error(request, "New PINs do not match.")
            elif len(new_pin) != 6 or not new_pin.isdigit():
                messages.error(request, "PIN must be exactly 6 digits.")
            else:
                profile.withdrawal_pin = new_pin
                profile.save()
                messages.success(request, "Withdrawal PIN updated successfully!")
                return redirect('security_settings')

    return render(request, 'users/security.html', {
        'profile': profile,
        'password_form': password_form
    })
    
@staff_member_required(login_url='staff_login')
def approve_withdrawal(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='withdrawal')
    order.status = 'withdrawn'
    order.save()
    messages.success(request, f"Withdrawal for {order.user.username} approved.")
    return redirect(f"{reverse('staffs')}?tab=withdrawals")

@staff_member_required(login_url='staff_login')
def reject_withdrawal(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='withdrawal')
    profile = order.user.profile
    with transaction.atomic():
        profile.balance += order.price
        profile.save()
        order.status = 'rejected'
        order.save()
    messages.warning(request, f"Withdrawal rejected. ${order.price} refunded.")
    return redirect(f"{reverse('staffs')}?tab=withdrawals")

@login_required(login_url='user_login')
def user_settings(request):
    return render(request, 'users/settings.html', {'profile': request.user.profile})

def error_404_view(request, exception):
    return render(request, '404.html', status=404)