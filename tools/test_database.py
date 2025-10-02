import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bankprocessor.settings')
django.setup()

from processor.models import ProcessingJob, BatchResult
from django.db import connection

def test_database():
    print("Probando conexión a la base de datos...")
    
    # 1. Verificar que las tablas existen
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('processor_processingjob', 'processor_batchresult')
        """)
        tables = cursor.fetchall()
        print(f"\nTablas encontradas: {[t[0] for t in tables]}")
    
    # 2. Verificar jobs existentes
    jobs = ProcessingJob.objects.all()
    print(f"\nJobs existentes: {jobs.count()}")
    for job in jobs:
        print(f"\nJob {job.id}:")
        print(f"- Status: {job.status}")
        print(f"- Progress: {job.progress}%")
        print(f"- Records: {job.processed_records}/{job.total_records}")
        
        # Verificar resultados por lotes
        results = BatchResult.objects.filter(job=job)
        print(f"- Batch results: {results.count()}")
        if results.exists():
            latest = results.order_by('-batch_number').first()
            print(f"  Último lote: {latest.batch_number}")
            print(f"  Accuracy: {latest.accuracy}")

if __name__ == "__main__":
    test_database()