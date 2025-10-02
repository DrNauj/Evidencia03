import os,sys
sys.path.insert(0, r'D:\Proyectos python\Evidencia03\bankprocessor')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','bankprocessor.settings')
import django
django.setup()
from processor.models import ProcessingJob
job = ProcessingJob.objects.create(batch_key='age', batch_size=100)
print('Created job', job.id)
manage = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'manage.py'))
python_exe = r'D:\Proyectos python\Evidencia03\venv\Scripts\python.exe'
print('Spawning run_job for', job.id)
import subprocess
p = subprocess.Popen([python_exe, manage, 'run_job', str(job.id)], cwd=os.path.dirname(manage))
print('PID', p.pid)
