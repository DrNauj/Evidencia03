from django.db import models
from django.utils import timezone

class ProcessingJob(models.Model):
    """Modelo para rastrear el estado del procesamiento por lotes"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('error', 'Error')
    ]
    
    batch_key = models.CharField(max_length=50, help_text='Columna usada para fragmentación')
    batch_size = models.IntegerField(help_text='Número de registros por lote')
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'Job {self.id} - {self.get_status_display()} ({self.batch_key})'

    @property
    def progress(self):
        """Calcula el progreso como porcentaje"""
        if self.total_records == 0:
            return 0
        return round((self.processed_records / self.total_records) * 100, 2)

class BatchResult(models.Model):
    """Modelo para almacenar resultados de cada lote procesado"""
    
    job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name='results')
    batch_number = models.IntegerField()
    records_processed = models.IntegerField()
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    confusion_matrix = models.JSONField()
    processing_time = models.FloatField(help_text='Tiempo de procesamiento en segundos')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['batch_number']
        unique_together = ['job', 'batch_number']

    def __str__(self):
        return f'Batch {self.batch_number} de Job {self.job_id}'
