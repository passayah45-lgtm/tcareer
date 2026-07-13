from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserRole


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT serializer to include user data in the token payload
    and in the response. Frontend gets user info on login without a second API call.
    """

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        token["role"] = user.role
        token["is_verified"] = user.is_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation returned in API responses."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "avatar_url",
            "role",
            "is_verified",
            "created_at",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    """
    Validates registration input. Intentionally not a ModelSerializer
    because we control the exact fields and validation logic here.
    """

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )
    full_name = serializers.CharField(min_length=2, max_length=255)
    role = serializers.ChoiceField(
        choices=[
            UserRole.STUDENT,
            UserRole.INSTRUCTOR,
            UserRole.MENTOR,
            UserRole.RECRUITER,
        ],
        default=UserRole.STUDENT,
    )

    def validate_email(self, value: str) -> str:
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
            role=validated_data.get("role", UserRole.STUDENT),
        )


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_new_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs.pop("new_password_confirm"):
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return attrs


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "avatar_url"]

    def validate_full_name(self, value: str) -> str:
        return value.strip()


class GoogleAuthSerializer(serializers.Serializer):
    """Receives the Google ID token from the frontend and validates it."""

    id_token = serializers.CharField()
