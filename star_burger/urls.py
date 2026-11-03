from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import include, path

from . import settings


def rollbar_test(request):
    1 / 0


def test_error(request):
    a = None
    a.hello()  # This will raise AttributeError
    return HttpResponse("This will not be reached")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", render, kwargs={"template_name": "index.html"}, name="start_page"),
    path("api/", include("foodcartapp.urls")),
    path("manager/", include("restaurateur.urls")),
    path("rollbar-test/", rollbar_test),
    path("test-error/", test_error, name="test_error"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path(r"__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
