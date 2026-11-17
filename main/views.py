"""Views for local account authentication."""

from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse


class FaraXLoginView(LoginView):
    """Sign in and return to a safe destination, if one was requested."""

    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        """Sign in without inventing a default post-login destination."""
        login(self.request, form.get_user())
        return HttpResponseRedirect(self.get_redirect_url() or reverse("login"))
