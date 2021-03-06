from django.contrib.auth.decorators import login_required
from user_management.models import User
from django.shortcuts import render


@login_required
def homepage(request):
    context = {}
    email = request.user.email
    user = User.objects.get(email=email)
    context['user_type'] = user.user_type
    print(user.user_type)
    return render(request, 'homepage.html', context)
    # if user.user_type == 'CUSTOMER':
    #     return render(request, 'homepage.html', context)
    # elif user.user_type == 'T3':
    #     return render(request, 't3_employee_home.html')
    # elif user.user_type == 'T2':
    #     return render(request, 't2_employee_home.html', context)
    # return render(request, 'employee_home.html')
