from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse


from .serializers import RegisterSerializer, LoginSerializer
from django.contrib.auth import get_user_model
User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class LoginView(APIView):

    def post(self,request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            response = JsonResponse({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            })
            response.set_cookie( #refresh token in httponly
                key='refresh_token',
                value=str(refresh),
                httponly=True,
                secure=False,  # only in prod
                samesite='Lax'
            )
            response.set_cookie( #access token in httponly
                key='access_token',
                value=str(refresh.access_token),
                httponly=True,
                secure=False,
                samesite='Lax'
            )
            return response
        return Response({'detail': 'invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
            except Exception:
                pass
        response = JsonResponse({
            "detail": "Logged out successfully.",
            "redirect": "/login" #Redirect to login page after logout
            }) 
        response.delete_cookie('refresh_token')
        response.delete_cookie('access_token')
        return response