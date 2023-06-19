from cProfile import Profile
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.utils.safestring import mark_safe
from .forms import AddGroupMemberForm, AdminVerificationRequestForm, RemoveGroupMemberForm, UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage, send_mail
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.models import User
from .tokens import account_activation_token
from .models import Group

def activateEmail(request, user, email):
    mail_subject = 'Activate your account.'
    message = render_to_string('users/acc_active_email.html', {
        'user': user,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[email])
    username = escape(user.username)
    if email.send():
        messages.success(request, mark_safe(f'Dear <b>{username}</b>, please check your email to activate your account.'))
    else:
        messages.error(request, 'There was an error sending the email. Please try again.')

def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Thank you for your email confirmation. Now you can login to your account.')
    else:
        messages.error(request, 'Activation link is invalid. Please try again.')

    return redirect('users:login')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect('users:login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        admin_verification_form = AdminVerificationRequestForm(request.POST)
        agm_form = AddGroupMemberForm(request.POST)
        rgm_form = RemoveGroupMemberForm(request.POST)

        if 'update_profile' in request.POST and u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('users:profile')
        
        elif admin_verification_form.is_valid():
            group_name = admin_verification_form.cleaned_data.get('group_name')
            institution = admin_verification_form.cleaned_data.get('institution')

            # Send an email to the admin
            send_mail(
                'ChemStats Group Verification Request',
                f'Dear administrator,\n\n{request.user.username} ({request.user.email}) requested verification as admin for the {group_name} at {institution}.\n\n -ChemStats Backend',
                'elijones1568@gmail.com',
                ['elijones1568@gmail.com'],  # Change this to your email
                fail_silently=False,
            )
            messages.success(request, 'Verification request sent!')
            return redirect('users:profile')
        
        # Handle adding group member
        elif 'add_group_member' in request.POST and agm_form.is_valid():
            username_or_email = agm_form.cleaned_data['username_or_email']
            # Logic to add group member
            try:
                # Find user by username or email
                user_to_add = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
                user_to_add.profile.group = request.user.profile.group
                user_to_add.profile.save()
                messages.success(request, 'Member added to group!')
            except User.DoesNotExist:
                messages.error(request, 'User not found!')
            return redirect('users:profile')

        # Handle removing group member
        elif 'remove_group_member' in request.POST and rgm_form.is_valid():
            username_or_email = rgm_form.cleaned_data['username_or_email']
            # Logic to remove group member
            try:
                # Find user by username or email
                user_to_remove = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
                if user_to_remove.profile.group == request.user.profile.group:
                    user_to_remove.profile.group = None
                    user_to_remove.profile.save()
                    messages.error(request, 'Member removed from group!')
                else:
                    messages.error(request, 'User is not a member of your group!')
            except User.DoesNotExist:
                messages.error(request, 'User not found!')
            return redirect('users:profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
        admin_verification_form = AdminVerificationRequestForm()
        agm_form = AddGroupMemberForm()
        rgm_form = RemoveGroupMemberForm()

    # Get current group members if the user is a group admin
    current_group_members = None
    try:
        group = Group.objects.get(admin=request.user)
        current_group_members = group.profile_set.all()  # Access the related profiles
    except Group.DoesNotExist:
        pass

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'admin_verification_form': admin_verification_form,
        'agm_form': agm_form,
        'rgm_form': rgm_form,
        'current_group_members': current_group_members,
    }
    
    return render(request, 'users/profile.html', context)
