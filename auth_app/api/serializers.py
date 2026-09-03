from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates registration data and creates an inactive user."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "confirmed_password"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"validators": []},
        }

    def validate_email(self, value):
        """Rejects duplicate emails without revealing that they exist."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Please check your input and try again.")
        return value

    def validate(self, attrs):
        """Ensures both password fields match."""
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError(
                {"error": "Please check your input and try again."}
            )
        return attrs

    def create(self, validated_data):
        """Creates the user with the email doubling as username."""
        validated_data.pop("confirmed_password")
        email = validated_data["email"]
        return User.objects.create_user(
            username=email, email=email, password=validated_data["password"]
        )


class LoginSerializer(serializers.Serializer):
    """Validates login credentials and returns the matching user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticates the credentials and attaches the user."""
        user = authenticate(username=attrs["email"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError(
                {"detail": "Please check your input and try again."}
            )
        attrs["user"] = user
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Validates the email address for a password reset request."""

    email = serializers.EmailField()


class PasswordConfirmSerializer(serializers.Serializer):
    """Validates the new password and its confirmation."""

    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Ensures both passwords match and meet Django's requirements."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"error": "Please check your input and try again."}
            )
        validate_password(attrs["new_password"])
        return attrs
