from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ambulances.models import AmbulanceRequest, RequestStatus
from apps.hospitals.models import Ambulance, Hospital

from .permissions import IsCitizen, IsOwningHospitalStaffOrAdmin
from .serializers import (
    AcceptRequestSerializer,
    AmbulanceRequestCreateSerializer,
    AmbulanceRequestDetailSerializer,
    AmbulanceSerializer,
    HospitalAvailabilityUpdateSerializer,
    HospitalSerializer,
)


class HospitalViewSet(viewsets.ModelViewSet):
    """
    Public-ish read access (any logged in user, any role) for browsing
    hospitals - this is what the citizen search page (Step 7) calls.
    Editing is locked down to admins and the staff of that specific
    hospital, via IsOwningHospitalStaffOrAdmin.
    """
    queryset = Hospital.objects.filter(is_active=True)
    serializer_class = HospitalSerializer
    permission_classes = [IsOwningHospitalStaffOrAdmin]

    def get_serializer_class(self):
        # staff hitting PATCH only get the 4-field availability serializer,
        # not the full one - keeps them from editing name/address/etc here
        if self.action in ('update', 'partial_update'):
            return HospitalAvailabilityUpdateSerializer
        return HospitalSerializer


class AmbulanceViewSet(viewsets.ModelViewSet):
    queryset = Ambulance.objects.all()
    serializer_class = AmbulanceSerializer
    permission_classes = [IsOwningHospitalStaffOrAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        hospital_id = self.request.query_params.get('hospital')
        if hospital_id:
            qs = qs.filter(hospital_id=hospital_id)
        return qs


class AmbulanceRequestViewSet(viewsets.ModelViewSet):
    """
    - citizens: only see/create their own requests
    - hospital staff: see pending (unassigned) requests plus whatever's
      already assigned to their hospital, so they can act on them
    - admin: sees everything
    """
    queryset = AmbulanceRequest.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return AmbulanceRequestCreateSerializer
        return AmbulanceRequestDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsCitizen()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.is_citizen:
            return qs.filter(citizen=user)

        if user.is_hospital_staff:
            profile = getattr(user, 'hospitalstaffprofile', None)
            if profile is None:
                return qs.none()
            return qs.filter(models_q_for_staff(profile.hospital_id))

        # admin / health authority sees all
        return qs

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        req = get_object_or_404(AmbulanceRequest, pk=pk)

        profile = getattr(request.user, 'hospitalstaffprofile', None)
        if not request.user.is_hospital_staff or profile is None:
            return Response({'detail': 'Only hospital staff can accept requests.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = AcceptRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ambulance = Ambulance.objects.get(pk=serializer.validated_data['ambulance_id'])

        try:
            req.accept(hospital=profile.hospital, ambulance=ambulance, staff_user=request.user)
        except DjangoValidationError as e:
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AmbulanceRequestDetailSerializer(req).data)

    @action(detail=True, methods=['post'], url_path='mark-dispatched')
    def mark_dispatched(self, request, pk=None):
        return self._run_transition(request, pk, 'mark_dispatched')

    @action(detail=True, methods=['post'], url_path='mark-completed')
    def mark_completed(self, request, pk=None):
        return self._run_transition(request, pk, 'mark_completed')

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        return self._run_transition(request, pk, 'cancel')

    def _run_transition(self, request, pk, method_name):
        req = get_object_or_404(AmbulanceRequest, pk=pk)

        # citizens can only cancel their own request, staff/admin can do
        # any of the transitions on requests tied to their hospital
        is_owner_citizen = request.user.is_citizen and req.citizen_id == request.user.id
        is_staff_or_admin = request.user.is_hospital_staff or request.user.is_admin_role

        if method_name == 'cancel':
            allowed = is_owner_citizen or is_staff_or_admin
        else:
            allowed = is_staff_or_admin

        if not allowed:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            getattr(req, method_name)()
        except DjangoValidationError as e:
            return Response({'detail': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AmbulanceRequestDetailSerializer(req).data)


def models_q_for_staff(hospital_id):
    # small helper - staff should see unassigned pending requests (so they
    # can accept them) plus anything already tied to their own hospital
    from django.db.models import Q
    return Q(hospital__isnull=True, status=RequestStatus.PENDING) | Q(hospital_id=hospital_id)