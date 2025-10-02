import logging
import time
import os
from functools import wraps
from django.utils import timezone

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('spark_performance.log'),
        logging.StreamHandler()
    ]
)

def monitor_performance(func):
    """Decorador para monitorear el rendimiento de funciones"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Obtener memoria inicial
        try:
            import psutil
        except Exception:
            logging.warning(
                "psutil no está disponible. Se usará un fallback que devuelve 0 MB. "
                "Instale psutil (`pip install psutil`) y añádalo a requirements.txt (por ejemplo: psutil>=5.8.0) "
                "para obtener mediciones de memoria reales."
            )

            class _DummyMI:
                def __init__(self):
                    self.rss = 0

            class _DummyProcess:
                def __init__(self, pid):
                    self.pid = pid

                def memory_info(self):
                    return _DummyMI()

            class _DummyPsutilModule:
                Process = _DummyProcess

            psutil = _DummyPsutilModule()

        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            success = False
            logging.error(f"Error en {func.__name__}: {str(e)}")
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time
            mem_after = process.memory_info().rss / 1024 / 1024
            mem_diff = mem_after - mem_before
            
            logging.info(
                f"Función: {func.__name__}\n"
                f"Duración: {duration:.2f} segundos\n"
                f"Memoria inicial: {mem_before:.1f} MB\n"
                f"Memoria final: {mem_after:.1f} MB\n"
                f"Diferencia memoria: {mem_diff:+.1f} MB\n"
                f"Estado: {'Éxito' if success else 'Error'}"
            )
        
        return result
    return wrapper

def log_spark_metrics(spark, stage_name):
    """Registra métricas de Spark"""
    try:
        metrics = {
            "Ejecutores activos": spark.sparkContext._jsc.sc().getExecutorMemoryStatus().size(),
            "Tareas pendientes": len(spark.sparkContext._jsc.sc().dagScheduler().waitingStages()),
            "Tareas activas": len(spark.sparkContext._jsc.sc().dagScheduler().runningStages()),
        }
        
        logging.info(f"Métricas Spark - {stage_name}:")
        for metric, value in metrics.items():
            logging.info(f"{metric}: {value}")
    except Exception as e:
        logging.warning(f"No se pudieron obtener métricas de Spark: {str(e)}")

def update_job_progress(job, current, total, stage=None):
    """Actualiza el progreso del trabajo"""
    try:
        progress = (current / total) * 100 if total > 0 else 0
        # Escribir processed_records para que la propiedad progress funcione
        job.processed_records = int(current)
        if stage:
            job.current_stage = stage
        job.last_update = timezone.now()
        job.save()
        
        logging.info(
            f"Progreso del trabajo {job.id}: "
            f"{progress:.1f}% ({current}/{total}) - {stage or 'sin etapa'}"
        )
    except Exception as e:
        logging.error(f"Error actualizando progreso: {str(e)}")