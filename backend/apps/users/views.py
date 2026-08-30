from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RegistrationSerializer, LoginSerializer, SafeUserSerializer


class RegistrationView(APIView):
    """
    API endpoint for user registration.
    
    POST /api/auth/register/
    
    Creates a new User and UserProfile with email and password.
    Returns safe user information (id, email) on success.
    """
    permission_classes = []  # Allow any user to register

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            # Return safe user representation
            user_serializer = SafeUserSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API endpoint for user login.
    
    POST /api/auth/login/
    
    Validates email and password credentials.
    Returns safe user information on successful authentication.
    
    Note: This endpoint validates credentials only.
    JWT/token authentication will be implemented in Phase 3C.
    """
    permission_classes = []  # Allow any user to attempt login

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # Return safe user representation
            user_serializer = SafeUserSerializer(user)
            return Response(
                {'user': user_serializer.data},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
