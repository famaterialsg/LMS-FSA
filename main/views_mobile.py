from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.utils.timezone import now
from .models import UserActivityLog  # Log hoạt động nếu cần

class LoginAPIView(APIView):
    """
    API View cho mobile app - Đăng nhập.
    """
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)

            # Log hoạt động
            UserActivityLog.objects.create(
                user=user,
                activity_type='login',
                activity_details='User logged in via mobile app',
                activity_timestamp=now()
            )

            return Response(
                {
                    "message": "Login successful.",
                    "token": token.key,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED
        )
