from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.accounts.decorators import role_required
from apps.accounts.forms import AdminCreateHospitalStaffForm
from apps.accounts.models import User, UserRole
from apps.ambulances.forms import AmbulanceRequestForm
from apps.ambulances.models import AmbulanceRequest, RequestStatus
from apps.hospitals.forms import AmbulanceForm, HospitalAvailabilityForm
from apps.hospitals.models import Ambulance, AmbulanceStatus, Hospital, HospitalStaffProfile, HospitalType


def home(request):
    user = request.user

    if not user.is_authenticated:
        featured_hospitals = Hospital.objects.filter(is_active=True)[:3]
        return render(request, 'public_landing.html', {'featured_hospitals': featured_hospitals})

    if user.is_citizen:
        return redirect('dashboard:citizen_hospitals')

    if user.is_hospital_staff:
        return redirect('dashboard:staff_dashboard')

    if user.is_admin_role:
        return redirect('dashboard:admin_dashboard')

    return redirect('accounts:profile')


@role_required(UserRole.CITIZEN)
def citizen_hospital_list(request):
    from apps.hospitals.utils import haversine_km

    search = request.GET.get('search', '').strip()
    hospital_type = request.GET.get('hospital_type', '').strip()
    beds_only = request.GET.get('beds_only') == '1'
    icu_only = request.GET.get('icu_only') == '1'
    ambulance_only = request.GET.get('ambulance_only') == '1'
    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')

    hospitals = Hospital.objects.filter(is_active=True)

    if search:
        hospitals = hospitals.filter(name__icontains=search) | hospitals.filter(city__icontains=search)
        hospitals = hospitals.distinct()

    if hospital_type:
        hospitals = hospitals.filter(hospital_type=hospital_type)

    if beds_only:
        hospitals = hospitals.filter(available_beds__gt=0)

    if icu_only:
        hospitals = hospitals.filter(available_icu_beds__gt=0)

    if ambulance_only:
        hospitals = [h for h in hospitals if h.available_ambulance_count > 0]

    hospitals = list(hospitals)

    if user_lat and user_lng:
        try:
            user_lat_f, user_lng_f = float(user_lat), float(user_lng)
            for h in hospitals:
                h.distance_km = round(haversine_km(user_lat_f, user_lng_f, h.latitude, h.longitude), 1)
            hospitals.sort(key=lambda h: h.distance_km)
        except (ValueError, TypeError):
            pass

    hospital_map_data = [
        {
            'id': h.id,
            'name': h.name,
            'lat': float(h.latitude),
            'lng': float(h.longitude),
            'beds': h.available_beds,
            'icu': h.available_icu_beds,
            'status': h.overall_status,
            'url': reverse('dashboard:citizen_hospital_detail', args=[h.id]),
        }
        for h in hospitals
    ]

    AVERAGE_SPEED_KMH = 35

    ambulance_map_data = []
    for h in hospitals:
        for amb in h.ambulances.all():
            if amb.status == AmbulanceStatus.AVAILABLE:
                ambulance_map_data.append({
                    'vehicle_number': amb.vehicle_number,
                    'hospital_name': h.name,
                    'status': 'available',
                    'origin_lat': float(h.latitude),
                    'origin_lng': float(h.longitude),
                    'dest_lat': float(h.latitude),
                    'dest_lng': float(h.longitude),
                    'started_at': None,
                    'travel_seconds': 0,
                })
            elif amb.status == AmbulanceStatus.DISPATCHED:
                active_req = AmbulanceRequest.objects.filter(
                    assigned_ambulance=amb,
                    status__in=[RequestStatus.ACCEPTED, RequestStatus.DISPATCHED],
                ).first()

                if active_req and active_req.pickup_latitude and active_req.pickup_longitude:
                    dest_lat = float(active_req.pickup_latitude)
                    dest_lng = float(active_req.pickup_longitude)
                    distance_km = haversine_km(float(h.latitude), float(h.longitude), dest_lat, dest_lng)
                    travel_seconds = max(20, (distance_km / AVERAGE_SPEED_KMH) * 3600)
                    started_at = (active_req.accepted_at or timezone.now()).isoformat()
                else:
                    dest_lat = float(h.latitude) + 0.004
                    dest_lng = float(h.longitude) + 0.004
                    travel_seconds = 60
                    started_at = timezone.now().isoformat()

                ambulance_map_data.append({
                    'vehicle_number': amb.vehicle_number,
                    'hospital_name': h.name,
                    'status': 'dispatched',
                    'origin_lat': float(h.latitude),
                    'origin_lng': float(h.longitude),
                    'dest_lat': dest_lat,
                    'dest_lng': dest_lng,
                    'started_at': started_at,
                    'travel_seconds': travel_seconds,
                })

    return render(request, 'dashboard/citizen_hospitals.html', {
        'hospitals': hospitals,
        'hospital_map_data': hospital_map_data,
        'ambulance_map_data': ambulance_map_data,
        'search': search,
        'hospital_type': hospital_type,
        'beds_only': beds_only,
        'icu_only': icu_only,
        'ambulance_only': ambulance_only,
        'hospital_types': HospitalType.choices,
        'has_location': bool(user_lat and user_lng),
        'user_lat': user_lat,
        'user_lng': user_lng,
    })
@role_required(UserRole.CITIZEN)
def citizen_hospital_detail(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk, is_active=True)
    return render(request, 'dashboard/citizen_hospital_detail.html', {'hospital': hospital})


@role_required(UserRole.CITIZEN)
def ambulance_request_create(request):
    if request.method == 'POST':
        form = AmbulanceRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.citizen = request.user
            req.save()
            if req.hospital:
                messages.success(request, f'Your request was sent to {req.hospital.name}.')
            else:
                messages.success(request, 'Your ambulance request has been submitted.')
            return redirect('dashboard:request_detail', pk=req.pk)
    else:
        initial = {}
        hospital_id = request.GET.get('hospital')
        if hospital_id:
            initial['hospital'] = hospital_id
        form = AmbulanceRequestForm(initial=initial)

    return render(request, 'dashboard/request_ambulance.html', {'form': form})


@role_required(UserRole.CITIZEN)
def my_requests(request):
    requests_qs = AmbulanceRequest.objects.filter(citizen=request.user)
    return render(request, 'dashboard/my_requests.html', {'requests': requests_qs})


@role_required(UserRole.CITIZEN)
def request_detail(request, pk):
    req = get_object_or_404(AmbulanceRequest, pk=pk, citizen=request.user)
    return render(request, 'dashboard/request_detail.html', {'req': req})


def _get_staff_hospital(user):
    profile = getattr(user, 'hospitalstaffprofile', None)
    return profile.hospital if profile else None


@role_required(UserRole.HOSPITAL_STAFF)
def staff_dashboard(request):
    hospital = _get_staff_hospital(request.user)
    if hospital is None:
        return render(request, 'dashboard/staff_no_hospital.html')

    pending_count = AmbulanceRequest.objects.filter(
        Q(hospital__isnull=True, status=RequestStatus.PENDING) | Q(hospital=hospital, status=RequestStatus.PENDING)
    ).count()
    active_count = AmbulanceRequest.objects.filter(
        hospital=hospital, status__in=[RequestStatus.ACCEPTED, RequestStatus.DISPATCHED]
    ).count()

    if request.method == 'POST':
        form = HospitalAvailabilityForm(request.POST, instance=hospital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Availability updated.')
            return redirect('dashboard:staff_dashboard')
    else:
        form = HospitalAvailabilityForm(instance=hospital)

    return render(request, 'dashboard/staff_home.html', {
        'hospital': hospital,
        'pending_count': pending_count,
        'active_count': active_count,
        'form': form,
    })


@role_required(UserRole.HOSPITAL_STAFF)
def staff_update_availability(request):
    hospital = _get_staff_hospital(request.user)
    if hospital is None:
        return render(request, 'dashboard/staff_no_hospital.html')

    if request.method == 'POST':
        form = HospitalAvailabilityForm(request.POST, instance=hospital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Availability updated.')
            return redirect('dashboard:staff_dashboard')
    else:
        form = HospitalAvailabilityForm(instance=hospital)

    return render(request, 'dashboard/staff_update_availability.html', {'form': form, 'hospital': hospital})


@role_required(UserRole.HOSPITAL_STAFF)
def staff_incoming_requests(request):
    hospital = _get_staff_hospital(request.user)
    if hospital is None:
        return render(request, 'dashboard/staff_no_hospital.html')

    pending_requests = AmbulanceRequest.objects.filter(
        Q(hospital__isnull=True, status=RequestStatus.PENDING) | Q(hospital=hospital, status=RequestStatus.PENDING)
    )
    active_requests = AmbulanceRequest.objects.filter(
        hospital=hospital, status__in=[RequestStatus.ACCEPTED, RequestStatus.DISPATCHED]
    )
    available_ambulances = hospital.ambulances.filter(status=AmbulanceStatus.AVAILABLE)

    return render(request, 'dashboard/staff_requests.html', {
        'hospital': hospital,
        'pending_requests': pending_requests,
        'active_requests': active_requests,
        'available_ambulances': available_ambulances,
    })


@role_required(UserRole.HOSPITAL_STAFF)
def staff_accept_request(request, pk):
    hospital = _get_staff_hospital(request.user)
    if hospital is None:
        return render(request, 'dashboard/staff_no_hospital.html')

    req = get_object_or_404(AmbulanceRequest, pk=pk)

    if request.method == 'POST':
        ambulance_id = request.POST.get('ambulance_id')
        ambulance = get_object_or_404(Ambulance, pk=ambulance_id, hospital=hospital)
        try:
            req.accept(hospital=hospital, ambulance=ambulance, staff_user=request.user)
            messages.success(request, f'Request accepted — {ambulance.vehicle_number} is on the way.')
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))

    return redirect('dashboard:staff_requests')


@role_required(UserRole.HOSPITAL_STAFF)
def staff_transition_request(request, pk, action):
    hospital = _get_staff_hospital(request.user)
    if hospital is None:
        return render(request, 'dashboard/staff_no_hospital.html')

    req = get_object_or_404(AmbulanceRequest, pk=pk, hospital=hospital)

    method_map = {
        'dispatch': ('mark_dispatched', 'marked as dispatched'),
        'complete': ('mark_completed', 'marked as completed'),
        'cancel': ('cancel', 'cancelled'),
    }
    action_info = method_map.get(action)
    if action_info is None:
        messages.error(request, 'Unknown action.')
        return redirect('dashboard:staff_requests')

    method_name, success_label = action_info

    if request.method == 'POST':
        try:
            getattr(req, method_name)()
            messages.success(request, f'Request {success_label}.')
        except ValidationError as e:
            messages.error(request, ' '.join(e.messages))

    return redirect('dashboard:staff_requests')


@role_required(UserRole.HOSPITAL_STAFF)
def staff_manage_ambulances(request):
    hospital = _get_staff_hospital(request.user)
    if hospital is None:
        return render(request, 'dashboard/staff_no_hospital.html')

    ambulances = hospital.ambulances.all()

    if request.method == 'POST':
        form = AmbulanceForm(request.POST)
        if form.is_valid():
            ambulance = form.save(commit=False)
            ambulance.hospital = hospital
            ambulance.save()
            messages.success(request, f'Ambulance {ambulance.vehicle_number} added.')
            return redirect('dashboard:staff_ambulances')
    else:
        form = AmbulanceForm()

    return render(request, 'dashboard/staff_ambulances.html', {
        'hospital': hospital,
        'ambulances': ambulances,
        'form': form,
    })


@role_required(UserRole.HOSPITAL_STAFF)
def staff_update_ambulance_status(request, pk):
    hospital = _get_staff_hospital(request.user)
    if hospital is None:
        return render(request, 'dashboard/staff_no_hospital.html')

    ambulance = get_object_or_404(Ambulance, pk=pk, hospital=hospital)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(AmbulanceStatus.choices):
            ambulance.status = new_status
            ambulance.save()
            messages.success(request, f'{ambulance.vehicle_number} marked as {ambulance.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status.')

    return redirect('dashboard:staff_ambulances')


@role_required(UserRole.ADMIN)
def admin_dashboard(request):
    stats = {
        'total_hospitals': Hospital.objects.count(),
        'active_hospitals': Hospital.objects.filter(is_active=True).count(),
        'pending_verifications': User.objects.filter(is_verified=False).exclude(role=UserRole.CITIZEN).count(),
        'total_citizens': User.objects.filter(role=UserRole.CITIZEN).count(),
        'total_staff': User.objects.filter(role=UserRole.HOSPITAL_STAFF, is_verified=True).count(),
        'pending_requests': AmbulanceRequest.objects.filter(status=RequestStatus.PENDING).count(),
        'active_requests': AmbulanceRequest.objects.filter(
            status__in=[RequestStatus.ACCEPTED, RequestStatus.DISPATCHED]
        ).count(),
        'completed_requests': AmbulanceRequest.objects.filter(status=RequestStatus.COMPLETED).count(),
    }

    today = timezone.now().date()
    day_labels = []
    day_counts = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        day_labels.append(day.strftime('%a'))
        day_counts.append(AmbulanceRequest.objects.filter(requested_at__date=day).count())

    fleet_available = Ambulance.objects.filter(status=AmbulanceStatus.AVAILABLE).count()
    fleet_dispatched = Ambulance.objects.filter(status=AmbulanceStatus.DISPATCHED).count()
    fleet_maintenance = Ambulance.objects.filter(status=AmbulanceStatus.UNDER_MAINTENANCE).count()

    return render(request, 'dashboard/admin_home.html', {
        'stats': stats,
        'day_labels': day_labels,
        'day_counts': day_counts,
        'fleet_available': fleet_available,
        'fleet_dispatched': fleet_dispatched,
        'fleet_maintenance': fleet_maintenance,
    })


@role_required(UserRole.ADMIN)
def admin_pending_accounts(request):
    pending_users = User.objects.filter(is_verified=False).exclude(role=UserRole.CITIZEN)
    unlinked_staff = User.objects.filter(
        role=UserRole.HOSPITAL_STAFF, is_verified=True, hospitalstaffprofile__isnull=True,
    )
    hospitals = Hospital.objects.filter(is_active=True)
    return render(request, 'dashboard/admin_pending_accounts.html', {
        'pending_users': pending_users,
        'unlinked_staff': unlinked_staff,
        'hospitals': hospitals,
    })


@role_required(UserRole.ADMIN)
def admin_verify_account(request, pk):
    user_to_verify = get_object_or_404(User, pk=pk, is_verified=False)

    if request.method == 'POST':
        user_to_verify.is_verified = True
        user_to_verify.save()

        if user_to_verify.role == UserRole.HOSPITAL_STAFF:
            hospital_id = request.POST.get('hospital_id')
            position = request.POST.get('position', '').strip()
            if hospital_id:
                hospital = get_object_or_404(Hospital, pk=hospital_id)
                HospitalStaffProfile.objects.update_or_create(
                    user=user_to_verify,
                    defaults={'hospital': hospital, 'position': position},
                )

        messages.success(request, f'{user_to_verify.username} has been verified.')

    return redirect('dashboard:admin_pending_accounts')


@role_required(UserRole.ADMIN)
def admin_reject_account(request, pk):
    user_to_reject = get_object_or_404(User, pk=pk, is_verified=False)
    if request.method == 'POST':
        username = user_to_reject.username
        user_to_reject.delete()
        messages.success(request, f'Account "{username}" was rejected and removed.')
    return redirect('dashboard:admin_pending_accounts')


@role_required(UserRole.ADMIN)
def admin_hospital_list(request):
    hospitals = Hospital.objects.all()
    return render(request, 'dashboard/admin_hospitals.html', {'hospitals': hospitals})


@role_required(UserRole.ADMIN)
def admin_toggle_hospital_active(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    if request.method == 'POST':
        hospital.is_active = not hospital.is_active
        hospital.save()
        state = 'active' if hospital.is_active else 'inactive'
        messages.success(request, f'{hospital.name} is now {state}.')
    return redirect('dashboard:admin_hospitals')


@role_required(UserRole.ADMIN)
def admin_create_staff_account(request):
    if request.method == 'POST':
        form = AdminCreateHospitalStaffForm(request.POST)
        if form.is_valid():
            new_user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                role=UserRole.HOSPITAL_STAFF,
                is_verified=True,
            )
            HospitalStaffProfile.objects.create(
                user=new_user,
                hospital=form.cleaned_data['hospital'],
                position=form.cleaned_data['position'],
            )
            messages.success(
                request,
                f'Hospital staff account "{new_user.username}" created and linked to '
                f'{form.cleaned_data["hospital"].name}.'
            )
            return redirect('dashboard:admin_pending_accounts')
    else:
        form = AdminCreateHospitalStaffForm()

    return render(request, 'dashboard/admin_create_staff.html', {'form': form})


@role_required(UserRole.ADMIN)
def admin_link_staff_to_hospital(request, pk):
    staff_user = get_object_or_404(User, pk=pk, role=UserRole.HOSPITAL_STAFF)

    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        position = request.POST.get('position', '').strip()
        if hospital_id:
            hospital = get_object_or_404(Hospital, pk=hospital_id)
            HospitalStaffProfile.objects.update_or_create(
                user=staff_user,
                defaults={'hospital': hospital, 'position': position},
            )
            messages.success(request, f'{staff_user.username} linked to {hospital.name}.')
        else:
            messages.error(request, 'Please choose a hospital.')

    return redirect('dashboard:admin_pending_accounts')