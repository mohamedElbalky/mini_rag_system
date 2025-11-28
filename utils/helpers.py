from rest_framework.response import Response


def create_response(success: bool, message: str, data=None, errors=None, status_code=200):
    response = {
        'success': success,
        'message': message,
    }
    if data is not None:
        response['data'] = data
    if errors is not None:
        response['errors'] = errors
    return Response(response, status=status_code)
