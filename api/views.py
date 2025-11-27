from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from utils.helpers import create_response

from .serializers import UserRegistrationSerializer, UserSerializer



# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user
    """
    try:
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return create_response(
                success=True,
                message='User registered successfully',
                data={
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                },
                status_code=status.HTTP_201_CREATED
            )
        
        return create_response(
            success=False,
            message='Registration failed',
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return create_response(
            success=False,
            message='An error occurred during registration',
            errors=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return JWT tokens
    """
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return create_response(
                success=False,
                message='Username and password are required',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            
            return create_response(
                success=True,
                message='Login successful',
                data={
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                },
                status_code=status.HTTP_200_OK
            )
        
        return create_response(
            success=False,
            message='Invalid credentials',
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    except Exception as e:
        return create_response(
            success=False,
            message='An error occurred during login',
            errors=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
