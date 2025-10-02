import os
from celery import Celery

# Configurar variables de entorno para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bankprocessor.settings')

# Crear instancia de Celery
app = Celery('bankprocessor')

# Usar configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas en todas las apps Django registradas
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')