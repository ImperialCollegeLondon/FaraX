"""Authentication helpers for application views."""

from collections.abc import Callable
from functools import wraps
from typing import Concatenate

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse


def admin_required[**P](
    view: Callable[Concatenate[HttpRequest, P], HttpResponse],
) -> Callable[Concatenate[HttpRequest, P], HttpResponse]:
    """Require authentication and membership of the Admin role."""

    @login_required
    @wraps(view)
    def wrapped(
        request: HttpRequest, *args: P.args, **kwargs: P.kwargs
    ) -> HttpResponse:
        if not request.user.is_authenticated or not request.user.is_admin:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped
