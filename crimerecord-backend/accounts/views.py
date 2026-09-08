import bcrypt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from cases.models import Users


# ─────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):

    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    selected_role = request.data.get('role', '').lower()

    if not username or not password:

        return Response(
            {'detail': 'Username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:

        user = Users.objects.get(
            username__iexact=username,
            is_active=1
        )

    except Users.DoesNotExist:

        return Response(
            {'detail': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:

        password_matches = bcrypt.checkpw(
            password.encode('utf-8'),
            user.password_hash.encode('utf-8')
        )

    except Exception:

        password_matches = False

    if not password_matches:

        return Response(
            {'detail': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # ROLE CHECK
    if selected_role and user.role.lower() != selected_role:

        return Response(
            {'detail': 'Incorrect role selected.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # SESSION STORAGE
    request.session['user_id'] = user.pk
    request.session['username'] = user.username
    request.session['role'] = user.role

    return Response({
        'user_id': user.pk,
        'username': user.username,
        'role': user.role,
        'name': user.full_name,
    })


# ─────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):

    request.session.flush()

    return Response({
        'detail': 'Logged out successfully.'
    })


# ─────────────────────────────────────────────────────────────
# CURRENT USER
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def me(request):

    user_id = request.session.get('user_id')

    if not user_id:

        return Response(
            {'detail': 'Not authenticated.'},
            status=401
        )

    try:

        user = Users.objects.get(
            pk=user_id,
            is_active=1
        )

    except Users.DoesNotExist:

        request.session.flush()

        return Response(
            {'detail': 'User not found.'},
            status=401
        )

    return Response({
        'user_id': user.pk,
        'username': user.username,
        'role': user.role,
        'name': user.full_name,
        'email': user.email or '',
        'is_staff': user.role in ('officer', 'admin'),
    })


# ─────────────────────────────────────────────────────────────
# REGISTER
# ─────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):

    username  = request.data.get('username', '').strip()
    password  = request.data.get('password', '')
    password2 = request.data.get('password2', '')
    full_name = request.data.get('full_name', username)
    email     = request.data.get('email', '')

    role = request.data.get('role', 'citizen').lower()

    # SAFETY VALIDATION
    if role not in ['citizen', 'officer']:
        role = 'citizen'

    errors = {}

    if not username:
        errors['username'] = ['This field is required.']

    if not password:
        errors['password'] = ['This field is required.']

    if len(password) < 6:
        errors['password'] = ['Password must be at least 6 characters.']

    if password != password2:
        errors['password2'] = ['Passwords do not match.']

    if username and Users.objects.filter(
        username__iexact=username
    ).exists():

        errors['username'] = ['Username already taken.']

    if errors:
        return Response(errors, status=400)

    from django.utils import timezone

    hashed = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    user = Users.objects.create(
        username      = username,
        password_hash = hashed,
        role          = role,
        full_name     = full_name or username,
        email         = email or None,
        is_active     = 1,
        created_at    = timezone.now(),
    )

    return Response({
        'user_id': user.pk,
        'username': user.username,
        'role': user.role,
    }, status=201)