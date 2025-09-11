from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    """DRF xatoliklarini oddiy JSON qilib qaytaradi."""
    response = exception_handler(exc, context)

    if response is None:
        return Response({"detail": "Server error"}, status=500)

    return response
