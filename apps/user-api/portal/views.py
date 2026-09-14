from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view

@api_view(["GET"])
def health(_request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({
        "status": "ok",
        "service": "quantum-platform-user-api",
        "database": "ok",
    })
