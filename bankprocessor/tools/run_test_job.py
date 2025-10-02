import os, sys, threading, time
sys.path.insert(0, r'd:\Proyectos python\Evidencia03\bankprocessor')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bankprocessor.settings')
import django
django.setup()
from processor.models import ProcessingJob, BatchResult
from django.utils import timezone

# Crear job de prueba
job = ProcessingJob.objects.create(batch_key='age', batch_size=100, status='pending')
print('Created job', job.id)

from processor.ml_processor import process_bank_data

def run():
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'bank.csv')
        process_bank_data(data_path, job)
    except Exception as e:
        print('Exception in process_bank_data:', repr(e))
        job.status = 'error'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()

t = threading.Thread(target=run)
# Run in thread to mimic real usage
t = threading.Thread(target=run)
t.start()
t.join(timeout=60)

job.refresh_from_db()
print('Job status after run:', job.status)
print('Error message:', job.error_message)
print('BatchResults:', BatchResult.objects.filter(job=job).count())
