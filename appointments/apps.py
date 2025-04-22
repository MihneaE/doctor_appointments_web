from django.apps import AppConfig


class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appointments'

    def ready(self):
        from django.contrib.auth.models import User
        import appointments.signals
        @property
        def is_doctor(self):
            return self.groups.filter(name="Doctor").exists()
        @property
        def is_client(self):
            return self.groups.filter(name="Client").exists()
        # Add the property to the User model
        User.add_to_class('is_doctor', is_doctor)
        User.add_to_class('is_client', is_client)
