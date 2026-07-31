# custom permissions for the api. mostly about making sure hospital staff
# can only touch their own hospital's data, and citizens can only see
# their own requests.

from rest_framework import permissions


class IsCitizen(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_citizen


class IsHospitalStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_hospital_staff


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin_role


class IsOwningHospitalStaffOrAdmin(permissions.BasePermission):
    """
    Used on Hospital/Ambulance objects - lets an admin edit anything, but a
    hospital staff account can only edit the hospital they're actually
    linked to (through HospitalStaffProfile). Read access is open to
    anyone logged in, this only kicks in for write operations.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (request.user.is_admin_role or request.user.is_hospital_staff)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_admin_role:
            return True

        if not request.user.is_hospital_staff:
            return False

        # obj could be a Hospital itself or something with a .hospital fk
        # (like Ambulance)
        target_hospital = obj if hasattr(obj, 'total_beds') else getattr(obj, 'hospital', None)

        profile = getattr(request.user, 'hospitalstaffprofile', None)
        if profile is None or target_hospital is None:
            return False
        return profile.hospital_id == target_hospital.id