from django.contrib import admin

from .models import Ambulance, Hospital, HospitalStaffProfile


class AmbulanceInline(admin.TabularInline):
    # so ambulances can be added directly from the hospital's own admin page
    model = Ambulance
    extra = 1
    fields = ('vehicle_number', 'driver_name', 'driver_phone', 'status')


class HospitalStaffInline(admin.TabularInline):
    model = HospitalStaffProfile
    extra = 0
    fields = ('user', 'position')
    autocomplete_fields = ['user']


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'hospital_type', 'city',
        'available_beds', 'total_beds',
        'available_icu_beds', 'total_icu_beds',
        'is_active',
    )
    list_filter = ('hospital_type', 'city', 'is_active')
    search_fields = ('name', 'address', 'city')
    inlines = [AmbulanceInline, HospitalStaffInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'hospital_type', 'is_active', 'image', 'description')
        }),
        ('Location', {
            'fields': ('address', 'city', 'latitude', 'longitude')
        }),
        ('Contact', {
            'fields': ('phone_number', 'email')
        }),
        ('Bed Availability (live)', {
            'fields': (('total_beds', 'available_beds'), ('total_icu_beds', 'available_icu_beds'))
        }),
    )

    def save_model(self, request, obj, form, change):
        # make sure the available <= total check still runs when saving
        # through the admin
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(Ambulance)
class AmbulanceAdmin(admin.ModelAdmin):
    list_display = ('vehicle_number', 'hospital', 'status', 'driver_name', 'driver_phone')
    list_filter = ('status', 'hospital')
    search_fields = ('vehicle_number', 'driver_name')


@admin.register(HospitalStaffProfile)
class HospitalStaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'hospital', 'position')
    list_filter = ('hospital',)
    autocomplete_fields = ['user', 'hospital']