from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CitizenSignUpForm, StyledAuthenticationForm


class SignUpView(CreateView):
    form_class = CitizenSignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        # no point showing signup form if already logged in
        if request.user.is_authenticated:
            return redirect('accounts:profile')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully. Please log in to continue.')
        return response


class CustomLoginView(LoginView):
    form_class = StyledAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()

        # hospital staff / health authority accounts need to be verified
        # by an admin before they're allowed to log in
        if not user.is_verified:
            messages.error(
                self.request,
                'Your account is pending verification by a system administrator. '
                'Please check back later.'
            )
            return self.form_invalid(form)

        auth_login(self.request, user)
        messages.success(self.request, f'Welcome back, {user.first_name or user.username}!')
        return redirect(self.get_success_url())


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


@login_required
def profile_view(request):
    # temporary landing page, will be replaced by the actual dashboards
    # once those are built
    return render(request, 'accounts/profile.html', {'user': request.user})