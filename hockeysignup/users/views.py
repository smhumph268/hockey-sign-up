from django.contrib.auth import views
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .forms import UserRegistrationForm, CustomLoginForm, UserDetailsForm
from .models import CustomUser


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

            messages.success(request, f'Your account has been created and is pending review. You can login once approved.')
            return HttpResponseRedirect(reverse('users:login'))
        else:
            for field in form.errors:
                if form[field].field.widget.attrs.keys().__contains__('class'):
                    form[field].field.widget.attrs['class'] += ' is-invalid'
    else:
        form = UserRegistrationForm()
        # Append css class to every field that contains errors.
        for field in form.errors:
            if form[field].field.widget.attrs.keys().__contains__('class'):
                form[field].field.widget.attrs['class'] += ' is-invalid'

    context = {'form': form}
    return render(request, 'users/register.html', context)


def user_profile(request, user_id):
    """
    Shows user profile values and allows user to edit values.
    """
    user = get_object_or_404(CustomUser, pk=user_id)
    if request.user.is_authenticated and request.user.id == user_id:
        # if this is a POST request we need to process the form data
        if request.method == "POST":
            # create a form instance and populate it with data from the request:
            form = UserDetailsForm(request.POST, instance=user, user=user)
            # check whether it's valid:
            if form.is_valid():
                # model form will update the record when form.save() is executed
                form.save()

                messages.success(request, f'Your details have been updated.')
                # redirect back to user's profile:
                return HttpResponseRedirect(reverse('users:profile', kwargs={'user_id': user_id}))
            else:
                return render(request, 'users/profile.html', {'form': form, 'requester_has_access': True})
        else:
            form = UserDetailsForm(user=user)
            return render(request, 'users/profile.html', {'form': form, 'requester_has_access': True})
    else:
        return render(request, 'users/profile.html', {'requester_has_access': False})
