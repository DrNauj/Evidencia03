from django.db import models

class CustomerPrediction(models.Model):
    # Datos personales
    age = models.IntegerField()
    job = models.CharField(max_length=50)
    marital = models.CharField(max_length=20)
    education = models.CharField(max_length=20)
    
    # Información financiera
    default = models.CharField(max_length=3)
    balance = models.IntegerField()
    housing = models.CharField(max_length=3)
    loan = models.CharField(max_length=3)
    
    # Información de campaña
    contact = models.CharField(max_length=20)
    day = models.IntegerField()
    month = models.CharField(max_length=10)
    duration = models.IntegerField()
    campaign = models.IntegerField()
    pdays = models.IntegerField()
    previous = models.IntegerField()
    poutcome = models.CharField(max_length=20)
    
    # Predicción
    prediction = models.CharField(max_length=3, null=True, blank=True)
    prediction_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Predicción para cliente {self.id} ({self.age} años, {self.job})"
    
    class Meta:
        verbose_name = "Predicción de Cliente"
        verbose_name_plural = "Predicciones de Clientes"
