from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import UserProfile

User = get_user_model()


class SafeUserSerializer(serializers.ModelSerializer):
    """
    Serializer that exposes only safe, non-sensitive user information.
    
    Never exposes password, password hash, or authentication secrets.
    """
    class Meta:
        model = User
        fields = ['id', 'email']
        read_only_fields = ['id', 'email']


class RegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    
    Handles email, password, and password confirmation.
    Creates both User and UserProfile in a transaction.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    password_confirmation = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_email(self, value):
        """
        Validate that email is not already registered.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        """
        Validate that passwords match and satisfy Django's password validators.
        """
        password = attrs.get('password')
        password_confirmation = attrs.get('password_confirmation')

        if password != password_confirmation:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        # Use Django's password validation framework
        try:
            validate_password(password)
        except serializers.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        """
        Create a new User and UserProfile atomically.
        
        Uses UserManager.create_user for proper password hashing.
        Password confirmation is never persisted.
        """
        email = validated_data['email']
        password = validated_data['password']

        with transaction.atomic():
            # Use UserManager for proper password hashing
            user = User.objects.create_user(
                email=email,
                password=password
            )

            # Create empty UserProfile (all fields are optional)
            UserProfile.objects.create(user=user)

        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    Validates email and password credentials.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        """
        Validate credentials using Django's authenticate().
        
        Returns a generic error for invalid credentials to avoid
        revealing whether the email exists separately from password correctness.
        """
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("Invalid email or password.")

        attrs['user'] = user
        return attrs
