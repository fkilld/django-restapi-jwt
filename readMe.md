# Building a Django REST API Authentication System with JWT

## Setting Up the Project

1. Create a new project folder and set up a virtual environment:

```bash
mkdir django_jwt_auth
cd django_jwt_auth
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the necessary packages:

```bash
pip install django djangorestframework djangorestframework-simplejwt
```

3. Create a Django project and app:

```bash
django-admin startproject core .
python manage.py startapp users
```

## Configuring JWT Authentication

Add the required settings to your `core/settings.py` file:

```python
INSTALLED_APPS = [
    # Django default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    
    # Local apps
    'users',
]

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

# JWT settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=180),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=50),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
}
```

## JWT Authentication Workflow

The JWT authentication flow works as follows:

1. User provides credentials (username/password)
2. Server validates credentials and issues two tokens:
   - Access token (short-lived)
   - Refresh token (longer-lived)
3. Client stores these tokens securely
4. Client sends the access token with each request requiring authentication
5. When the access token expires, client uses refresh token to get a new access token[2]

## Setting Up URL Endpoints

Create the JWT authentication endpoints in your `core/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
    TokenBlacklistView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('api/users/', include('users.urls')),
]
```

## Creating User Registration

Create a serializer for user registration in `users/serializers.py`:

```python
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
```

Create a view for user registration in `users/views.py`:

```python
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
from rest_framework.response import Response
from rest_framework import status

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        user = request.user
        content = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        return Response(content)
```

Create URL patterns for the users app in `users/urls.py`:

```python
from django.urls import path
from .views import RegisterView, UserProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]
```

## Creating Database and Running Migrations

Initialize your database:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Testing the JWT Authentication System

1. Run the development server:

```bash
python manage.py runserver
```

2. Register a new user:

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"ComplexPassword123!","password2":"ComplexPassword123!","first_name":"Test","last_name":"User"}'
```

3. Obtain access and refresh tokens:

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"ComplexPassword123!"}'
```

4. Access protected route using token:

```bash
curl -X GET http://localhost:8000/api/users/profile/ \
  -H "Authorization: Bearer "
```

5. Refresh token when it expires:

```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":""}'
```

6. Logout (blacklist refresh token):

```bash
curl -X POST http://localhost:8000/api/token/blacklist/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":""}'
```

7. Create a post:

```bash
curl -X POST http://localhost:8000/api/posts/ \
  -H "Authorization: Bearer " \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Post","content":"This is a test post"}'
```

8. Get all posts:

```bash
curl -X GET http://localhost:8000/api/posts/ \
  -H "Authorization: Bearer "
```

9. Delete a post:

```bash
curl -X DELETE http://localhost:8000/api/posts/1/ \
  -H "Authorization: Bearer "
```

10. Update a post:

```bash
curl -X PUT http://localhost:8000/api/posts/1/ \
  -H "Authorization: Bearer " \
  -H "Content-Type: application/json" \
  -d '{"title":"Updated Post","content":"This is an updated post"}'
```

11. Get a specific post:
    
```bash
curl -X GET http://localhost:8000/api/posts/1/ \
  -H "Authorization: Bearer "
```