from django.apps import AppConfig

class SortiesConfig(AppConfig):
    name = 'sorties'

    def ready(self):
        import sorties.signals
