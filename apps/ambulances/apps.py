from django.apps import AppConfig


class AmbulancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ambulances'
    label = 'ambulances'
    verbose_name = 'Ambulance Requests'

    def ready(self):
        import apps.ambulances.signals  # noqa: F401 - just registers the signal