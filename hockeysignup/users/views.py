from django.contrib.auth import views
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from .forms import UserRegistrationForm, CustomLoginForm


class UserLoginView(views.LoginView):
    authentication_form = CustomLoginForm
    template_name = 'users/login.html'


class UserLogoutView(views.LogoutView):
    template_name = 'users/logout.html'


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()

            messages.success(request, f'Your account has been created. You can log in now!')
            return HttpResponseRedirect(reverse('users:login'))
        else:
            for field in form.errors:
                form[field].field.widget.attrs['class'] += ' is-invalid'
    else:
        form = UserRegistrationForm()
        # Append css class to every field that contains errors.
        for field in form.errors:
            form[field].field.widget.attrs['class'] += ' my-css-class'

    context = {'form': form}
    return render(request, 'users/register.html', context)
