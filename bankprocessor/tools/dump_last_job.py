import os, sys
sys.path.insert(0, r'd:\Proyectos python\Evidencia03\bankprocessor')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bankprocessor.settings')
import django
django.setup()
from processor.models import ProcessingJob

j = ProcessingJob.objects.order_by('-started_at').first()
print('=== ENVIRONMENT ===')
print('JAVA_HOME=', os.environ.get('JAVA_HOME'))
print('HADOOP_HOME=', os.environ.get('HADOOP_HOME'))
print('PYSPARK_PYTHON=', os.environ.get('PYSPARK_PYTHON'))
print('PYSPARK_DRIVER_PYTHON=', os.environ.get('PYSPARK_DRIVER_PYTHON'))
print('DATA EXISTS:', os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'bank.csv')))
print('')
if not j:
    print('No ProcessingJob found')
    sys.exit(0)

print('=== LAST JOB ===')
print('id:', j.id)
print('status:', j.status)
print('started_at:', j.started_at)
print('processed_records:', j.processed_records)
print('total_records:', j.total_records)
print('error_message (repr):')
print('---START---')
print(repr(j.error_message))
print('---END---')

# If error_message contains a known spark socket issue, hint
if j.error_message and ('Connection reset by peer' in j.error_message or 'Python worker exited' in j.error_message):
    print('\nHINT: appears to be a PySpark worker/socket error. Consider running on WSL2/Linux or using local[1] and reducing parallelism.')
