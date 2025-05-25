from django.apps import AppConfig


class CoursesAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses_app'

    def ready(self):
        import courses_app.signals