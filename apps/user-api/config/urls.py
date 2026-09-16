from django.contrib import admin
from django.urls import include, path

from portal.views import home

from portal.metrics import metrics

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),

    # Standard Django/allauth browser flows.
    path("accounts/", include("allauth.urls")),

    # Future Astro User Portal API.
    path("_allauth/", include("allauth.headless.urls")),

    # Our own API.
    path("api/v1/", include("portal.api_urls")),

    # Django metric
    path("metrics", metrics, name="metrics"),
]
