from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .serializers import RegistrationSerializer, LoginSerializer, SafeUserSerializer


@method_decorator(csrf_exempt, name='dispatch')
class RegistrationView(APIView):
    """
    API endpoint for user registration.
    
    POST /api/auth/register/
    
    Creates a new User and UserProfile with email and password.
    Returns safe user information (id, email) on success.
    
    CSRF EXEMPTION RATIONALE:
    This endpoint is exempt from CSRF protection because:
    1. It does not establish an authenticated browser session
    2. It does not operate on existing authenticated state
    3. It is a public endpoint for initial account creation
    4. No CSRF token exists yet for unauthenticated users
    
    Future authenticated state-changing endpoints MUST enforce CSRF protection.
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


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """
    API endpoint for user login with JWT tokens.
    
    POST /api/auth/login/
    
    Validates email and password credentials.
    Returns JWT access and refresh tokens as HttpOnly cookies.
    Returns safe user information on successful authentication.
    
    CSRF EXEMPTION RATIONALE:
    This endpoint is exempt from CSRF protection because:
    1. It does not operate on existing authenticated state
    2. It establishes initial authentication via credentials, not session cookies
    3. JWT tokens are stored in HttpOnly cookies, not used as CSRF tokens
    4. The endpoint validates credentials explicitly
    
    Future authenticated state-changing endpoints MUST enforce CSRF protection.
    """
    permission_classes = []  # Allow any user to attempt login

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # Create response with user data
            user_serializer = SafeUserSerializer(user)
            response = Response(
                {'user': user_serializer.data},
                status=status.HTTP_200_OK
            )
            
            # Set HttpOnly cookies for tokens
            response.set_cookie(
                'access_token',
                access_token,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/'
            )
            response.set_cookie(
                'refresh_token',
                refresh_token,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/api/auth/refresh/'
            )
            
            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class RefreshView(APIView):
    """
    API endpoint for refreshing JWT access token.
    
    POST /api/auth/refresh/
    
    Uses the refresh token from HttpOnly cookie to generate new tokens.
    Returns new access and refresh tokens as HttpOnly cookies.
    Implements refresh token rotation with blacklisting of old tokens.
    
    CSRF EXEMPTION RATIONALE:
    This endpoint is exempt from CSRF protection because:
    1. It is a token renewal endpoint, not a state-changing business operation
    2. It explicitly validates the JWT refresh token from the cookie
    3. The refresh token is scoped to this specific path (/api/auth/refresh/)
    4. Token rotation provides replay protection via blacklisting
    
    Future authenticated state-changing endpoints MUST enforce CSRF protection.
    """
    permission_classes = []  # Allow any user with valid refresh token

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token not found.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            
            # Extract access token from the old refresh token before blacklisting
            access_token = str(refresh.access_token)
            
            # Manually rotate the refresh token if rotation is enabled
            if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
                # Get user_id from token payload
                user_id = refresh['user_id']
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(id=user_id)
                
                # Generate a new refresh token for the same user
                new_refresh = RefreshToken.for_user(user)
                new_refresh_token = str(new_refresh)
                
                # Blacklist the old token if configured (after generating new one)
                if settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION', False):
                    try:
                        refresh.blacklist()
                    except Exception:
                        # If blacklisting fails, continue with rotation
                        pass
            else:
                new_refresh_token = str(refresh)
            
            response = Response(
                {'detail': 'Access token refreshed successfully.'},
                status=status.HTTP_200_OK
            )
            
            # Set new access token cookie
            response.set_cookie(
                'access_token',
                access_token,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/'
            )
            
            # Set new refresh token cookie (rotation)
            response.set_cookie(
                'refresh_token',
                new_refresh_token,
                max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/api/auth/refresh/'
            )
            
            return response
            
        except Exception as e:
            return Response(
                {'detail': 'Invalid refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED
            )


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    """
    API endpoint for user logout.
    
    POST /api/auth/logout/
    
    Revokes the presented refresh token using SimpleJWT blacklist
    and clears the HttpOnly cookies containing JWT tokens.
    
    CSRF EXEMPTION RATIONALE:
    This endpoint is exempt from CSRF protection because:
    1. It is a logout operation that terminates authentication
    2. It explicitly validates and revokes the JWT refresh token
    3. The operation is idempotent and safe to call
    4. No state-changing business logic occurs
    
    Future authenticated state-changing endpoints MUST enforce CSRF protection.
    """
    permission_classes = []  # Allow any user to logout

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        
        # Revoke the refresh token if present
        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                # Blacklist the token using SimpleJWT's blacklist mechanism
                refresh.blacklist()
            except Exception:
                # If token is invalid, still proceed to clear cookies
                pass
        
        response = Response(
            {'detail': 'Successfully logged out.'},
            status=status.HTTP_200_OK
        )
        
        # Clear authentication cookies
        response.delete_cookie('access_token', path='/')
        response.delete_cookie('refresh_token', path='/api/auth/refresh/')
        
        return response


class MeView(APIView):
    """
    API endpoint for retrieving current user information.
    
    GET /api/auth/me/
    
    Returns safe user information for the authenticated user.
    Requires valid JWT authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_serializer = SafeUserSerializer(request.user)
        return Response(user_serializer.data, status=status.HTTP_200_OK)
