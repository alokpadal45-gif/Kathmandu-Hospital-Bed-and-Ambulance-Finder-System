from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import AmbulanceRequest


@admin.register(AmbulanceRequest)
class AmbulanceRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient_name', 'contact_number', 'status',
        'hospital', 'assigned_ambulance', 'requested_at',
    )
    list_filter = ('status', 'hospital')
    search_fields = ('patient_name', 'contact_number', 'pickup_address')
    readonly_fields = ('requested_at', 'accepted_at', 'dispatched_at', 'completed_at', 'cancelled_at')

    actions = ['mark_as_dispatched', 'mark_as_completed', 'mark_as_cancelled']

    @admin.action(description='Mark selected requests as dispatched')
    def mark_as_dispatched(self, request, queryset):
        count = 0
        for req in queryset:
            try:
                req.mark_dispatched()
                count += 1
            except ValidationError:
                # skip ones that aren't in the right state, don't blow up
                # the whole bulk action for one bad row
                continue
        self.message_user(request, f'{count} request(s) marked dispatched.')

    @admin.action(description='Mark selected requests as completed')
    def mark_as_completed(self, request, queryset):
        count = 0
        for req in queryset:
            try:
                req.mark_completed()
                count += 1
            except ValidationError:
                continue
        self.message_user(request, f'{count} request(s) marked completed.')

    @admin.action(description='Cancel selected requests')
    def mark_as_cancelled(self, request, queryset):
        count = 0
        for req in queryset:
            try:
                req.cancel()
                count += 1
            except ValidationError:
                continue
        self.message_user(request, f'{count} request(s) cancelled.')