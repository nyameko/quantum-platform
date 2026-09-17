from django.contrib import admin
from django.urls import include, path

from allauth.account.decorators import secure_admin_login

from portal.metrics import metrics
from portal.views import home
from portal.agent_admin import agent_history, agent_task

admin.autodiscover()
admin.site.login = secure_admin_login(admin.site.login)

urlpatterns = [
    path("", home, name="home"),
    path("admin/agent-runs/", admin.site.admin_view(agent_history), name="agent-history"),
    path("admin/agent-runs/<uuid:task_id>/", admin.site.admin_view(agent_task), name="agent-task"),
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
