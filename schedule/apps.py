from django.apps import AppConfig


class LabScheduleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "schedule"
    verbose_name = "Manajemen Jadwal"

    def ready(self):
        import schedule.admins
