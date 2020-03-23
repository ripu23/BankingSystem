from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from user_management.forms import RegistrationForm, LoginForm, EditForm, FundTransferForm
from django.contrib.auth.decorators import login_required, user_passes_test
from user_management.models import User, FundTransferRequest, employee_info_update, OverrideRequest

# Create your views here.


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    context = {}
    if request.POST:
        email = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=email, password=password)
        if user is not None:
            if user.is_active:
                form = LoginForm(request, data=request.POST)
                context['login_form'] = form
                is_valid_form = form.is_valid()
                if is_valid_form:
                    login(request, user)
                    return redirect('home')
                else:
                    context['otp_sent'] = True
                    return render(request, 'user_management/login.html', context)
            else:
                context['inactive'] = True
                form = LoginForm(request, data=request.POST)
                context['login_form'] = form
                return render(request, 'user_management/login.html', context)
        else:
            context['user_none'] = True
            form = LoginForm(request, data=request.POST)
            context['login_form'] = form
            return render(request, 'user_management/login.html', context)
    else:
        form = LoginForm()
        context['login_form'] = form
    return render(request, 'user_management/login.html', context)


def register_view(request):
    context = {}
    context['created'] = False
    if request.POST:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            email = form.cleaned_data.get("email")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(email=email, password=raw_password)
            # login(request, user)
            # return redirect('home')
            context['created'] = True
        else:
            context['registration_form'] = form
    else:  # GET REQUEST
        form = RegistrationForm()
        context['registration_form'] = form
    return render(request, 'user_management/register.html', context)


def logout_user(request):
    logout(request)
    context = {}
    form = LoginForm()
    context['login_form'] = form
    return redirect(request, 'user_management/login.html')


@login_required
def view_profile(request):
    if request.user.user_type == 'CUSTOMER':
        base_template_name = 'homepage.html'
    else:
        base_template_name = 'employee_home.html'
    context = {'user': request.user, 'base_template_name': base_template_name}
    return render(request, 'user_management/profile.html', context)


@login_required
def transfers(request):
    if request.POST:
        form = FundTransferForm(request.POST, request.user)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            context = {}
            context['request_received'] = True
            print('request_received')
            return redirect('home')
    else:
        context = {}
        form = FundTransferForm(instance=request.user)
        form.fields['from_account'].queryset = User.objects.filter(
            user_id=request.user.user_id)
        form.fields['to_account'].queryset = User.objects.exclude(
            user_id=request.user.user_id)
        context['transfer_form'] = form
        return render(request, 'user_management/transfers.html', context)


def employee_check(user):
    return user.user_type in ["T1", "T2", "T3"]


@login_required
@user_passes_test(employee_check)
def pendingFundTransfers(request):
    if request.POST:
        FundTransferRequest.objects.filter(request_id=int(
            request.POST['request_id'])).update(status=request.POST['status'])
        return render(request, 'user_management/pendingFundTransfers.html')
    context = {}
    context['pendingFundTransfersData'] = {
        'headers': [u'transactionId', u'from_name', u'to_name', u'amount', u'status', u'approve', u'reject'],
        'rows': []
    }
    for e in FundTransferRequest.objects.filter(status="NEW"):
        context['pendingFundTransfersData']['rows'].append([e.request_id,
                                                            e.from_account.first_name + " " + e.from_account.last_name,
                                                            e.to_account.first_name + " " + e.to_account.last_name,
                                                            e.amount,
                                                            e.status])
    return render(request, 'user_management/pendingFundTransfers.html', context)


@login_required
def edit_profile(request):
    if request.POST:
        form = EditForm(request.POST)
        if form.is_valid():
            data = request.POST.copy()
            user_id = int(request.user.user_id)

            num_results = employee_info_update.objects.filter(user_id=user_id, status='NEW').count()
            if num_results > 0:
                return render(request, 'employee_request_already_exists.html')

            new_entry = employee_info_update(user_id=user_id, email=data.get('email'), first_name=data.get('first_name'),
                                             last_name=data.get('last_name'), phone_number=data.get('phone_number'),
                                             gender=data.get('gender'), status='NEW')
            new_entry.save()

            instance = form.save(commit=False)
            instance.created_by = request.user
            instance.save()
            context = {}
            context['request_received'] = True
            return render(request, 'employee_edit_request_submitted.html', context)
    else:
        context = {}
        form = EditForm(instance=request.user)
        context['edit_form'] = form
        return render(request, 'user_management/edit_profile.html', context)

@login_required
def show_pending_employee_requests(request):
    if request.POST:
        employee_info_update.objects.filter(user_id=int(
            request.POST['user_id']), status='NEW').update(status=request.POST['status'])

        if request.POST['status'] == 'APPROVE':
            user_object = User.objects.get(user_id=int(request.POST['user_id']))
            user_object.email = request.POST['email_id']
            user_object.first_name = request.POST['first_name']
            user_object.last_name = request.POST['last_name']
            user_object.phone_number = request.POST['phone_number']
            user_object.gender = request.POST['gender']
            user_object.save()

        return render(request, 'user_management/pendingEmployeeRequests.html')
    context = {}
    context['employee_info_update_request'] = {
        'headers': [u'user_id', u'email', u'first_name', u'last_name', u'phone_number', u'gender', u'approve', u'reject'],
        'rows': []
    }

    for e in employee_info_update.objects.filter(status="NEW"):
        context['employee_info_update_request']['rows'].append([e.user_id, e.email,
                                                                e.first_name, e.last_name,
                                                                e.phone_number,
                                                                e.gender])
    return render(request, 'user_management/pendingEmployeeRequests.html', context)


@login_required
def technicalSupport(request):
    headers = [u"user_id", u"email", u"first_name", u"last_name", u"user_type"]

    users = [[getattr(user, header) for header in headers] for user in User.objects.all()
             if user.user_type in ["T1", "T2", "T3"]]

    context = {
        "users": {
            "headers": headers + ["Account Override"],
            "rows": users
        }
    }

    if request.POST:
        if request.POST["action"] == "REQUEST_ACCESS":
            from_id = request.user.user_id
            for_id = request.POST['user_id']
            print(OverrideRequest.objects.filter(requesting_id=from_id, for_id=for_id, status="NEW").count())
            if OverrideRequest.objects.filter(requesting_id=from_id, for_id=for_id, status="NEW").count() > 0:
                return render(request, 'employee_request_already_exists.html')
            else:
                new_request = OverrideRequest(requesting_id=from_id, for_id=for_id)
                new_request.save()

    return render(request, 'user_management/technicalSupport.html', context)
