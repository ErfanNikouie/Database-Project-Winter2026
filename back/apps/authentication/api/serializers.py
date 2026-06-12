from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class CurrentUserUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False)
    current_password = serializers.CharField(max_length=128, required=False)
    new_password = serializers.CharField(max_length=128, required=False)
    confirm_new_password = serializers.CharField(max_length=128, required=False)

    def validate(self, attrs):
        wants_password_change = any(
            attrs.get(key)
            for key in ("current_password", "new_password", "confirm_new_password")
        )
        if wants_password_change:
            required = ["current_password", "new_password", "confirm_new_password"]
            missing = [key for key in required if not attrs.get(key)]
            if missing:
                raise serializers.ValidationError(
                    f"Missing required fields for password change: {', '.join(missing)}"
                )
            if attrs["new_password"] != attrs["confirm_new_password"]:
                raise serializers.ValidationError("New passwords do not match")
        return attrs


