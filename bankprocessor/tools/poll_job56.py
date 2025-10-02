import time, sys, os
sys.path.insert(0, r'D:\Proyectos python\Evidencia03\bankprocessor')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','bankprocessor.settings')
import django
django.setup()
from processor.models import ProcessingJob
for i in range(15):
    j = ProcessingJob.objects.filter(id=56).first()
    if j and j.status != 'processing':
        print('Status after', i, 'seconds:', j.status)
        print('Error message:', j.error_message)
        break
    time.sleep(1)
else:
    j = ProcessingJob.objects.filter(id=56).first()
    print('Final status:', j.status if j else 'no job')
    print('Error message:', j.error_message if j else None)
