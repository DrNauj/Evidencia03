import logging
import os
from datetime import datetime

# Configurar logging
log_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(log_dir, 'logs', 'processing.log')

# Crear directorio de logs si no existe
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logger = logging.getLogger('processing')
logger.setLevel(logging.DEBUG)

# Handler para archivo
fh = logging.FileHandler(log_file)
fh.setLevel(logging.DEBUG)

# Handler para consola
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Formato
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

def log_job_status(job_id, status, progress=None, message=None):
    """Registra actualizaciones de estado del job"""
    logger.info(f"Job {job_id} - Status: {status} - Progress: {progress}% - Message: {message}")

def log_batch_result(job_id, batch_number, metrics):
    """Registra métricas de un lote procesado"""
    logger.info(f"Job {job_id} - Batch {batch_number} - Metrics: {metrics}")

def log_error(job_id, error_message, exception=None):
    """Registra errores en el procesamiento"""
    logger.error(f"Job {job_id} - Error: {error_message}", exc_info=exception)