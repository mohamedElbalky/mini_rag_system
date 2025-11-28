from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses
    """
    response = drf_exception_handler(exc, context)

    if response is not None:
        custom_response = {
            'success': False,
            'message': 'An error occurred',
            'errors': response.data
        }
        response.data = custom_response
    else:
        logger.error(f"Unhandled exception: {str(exc)}")
        custom_response = {
            'success': False,
            'message': 'An internal error occurred',
            'error': str(exc)
        }
        response = Response(custom_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response