from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q

from .models import Cases, Users
from .serializers import CaseSerializer
from .permissions import IsOfficerOrReadOnly

class CaseViewSet(viewsets.ModelViewSet):
    serializer_class   = CaseSerializer
    permission_classes = [IsOfficerOrReadOnly]

    def get_queryset(self):
        qs = Cases.objects.select_related(
            'crime_type', 'location', 'suspect', 'reported_by', 'assigned_to'
        ).all()

        status_filter = self.request.query_params.get('status')
        search        = self.request.query_params.get('search')
        reporter      = self.request.query_params.get('reporter')
        role          = self.request.session.get('role', '')
        user_id       = self.request.session.get('user_id')

        # --- RULE 1: The "My Reports" Private Dashboard ---
        if reporter == 'me' and user_id:
            # ONLY return cases reported by this specific citizen
            return qs.filter(reported_by_id=user_id).order_by('-created_at')

        # --- RULE 2: The Global Search Firewall ---
        if role not in ['officer', 'admin']:
            # If they are a citizen/public, actively strip out ALL "Pending Review" 
            # records from the global search.
            qs = qs.exclude(status='Pending Review')

        # --- Apply standard search & status filters ---
        if status_filter:
            qs = qs.filter(status=status_filter)

        if search:
            qs = qs.filter(
                Q(victim_name__icontains=search)          |   
                Q(suspect__name__icontains=search)        |
                Q(crime_type__name__icontains=search)     |
                Q(location__name__icontains=search)       |
                Q(description__icontains=search)
            )

        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        user_id = self.request.session.get('user_id')
        role = self.request.session.get('role', '')

        # Force Citizen reports into Pending status automatically
        if role == 'citizen':
            serializer.validated_data['status'] = 'Pending'
            serializer.validated_data['suspect'] = None

        if user_id:
            try:
                user = Users.objects.get(pk=user_id)
                serializer.save(reported_by=user)
                return
            except Users.DoesNotExist:
                pass
        serializer.save()

    # --- NEW: The 1-Click "Take Case" Action for Officers ---
    @action(detail=True, methods=['post'])
    def take_case(self, request, pk=None):
        role = request.session.get('role', '')
        if role not in ['officer', 'admin']:
            return Response({"detail": "Only officers can take cases."}, status=status.HTTP_403_FORBIDDEN)

        case = self.get_object()
        user_id = request.session.get('user_id')

        try:
            officer = Users.objects.get(pk=user_id)
            case.assigned_to = officer  # Auto-assign the officer
            case.status = 'Open'        # Upgrade status
            case.save()
            return Response({"detail": "Case assigned successfully.", "assigned_to": officer.full_name})
        except Users.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)