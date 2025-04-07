from django.apps import AppConfig


class VaruniConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'varuni'
def ready(self):
    import varuni.signals  # Replace `varuni` with your app name
