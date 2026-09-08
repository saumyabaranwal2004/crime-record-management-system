# cases/permissions.py
#
# WHY: The old permission class used request.user.is_authenticated and
# request.user.is_staff — both Django auth concepts.  Since we're not using
# Django's auth system at all, request.user is always AnonymousUser.
#
# Instead we check request.session['role'] which accounts/views.py sets on login.
# Role values from the DB: 'officer', 'admin', 'citizen'
#
# Public access (GET) is unrestricted.
# POST / PATCH / DELETE require role == 'officer' or 'admin'.

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOfficerOrReadOnly(BasePermission):
    """
    Public        → GET / HEAD / OPTIONS
    officer/admin → all methods (POST, PATCH, PUT, DELETE)
    citizen       → read-only (same as public)
    """

    def _is_officer(self, request) -> bool:
        role = request.session.get('role', '')
        return role in ('officer', 'admin')

    def has_permission(self, request, view):

    # Public read access
        if request.method in SAFE_METHODS:
            return True

        role = request.session.get('role', '')

    # Citizens can CREATE reports only
        if request.method == 'POST':
            return role in ('citizen', 'officer', 'admin')

    # Only officers/admins can edit/delete
        return role in ('officer', 'admin')
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return self._is_officer(request)