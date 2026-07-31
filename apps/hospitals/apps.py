from django.apps import AppConfig


class HospitalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.hospitals'
    label = 'hospitals'
    verbose_name = 'Hospitals & Resources'

    def ready(self):
        import apps.hospitals.signals  # noqa: F401 - just registers the signal