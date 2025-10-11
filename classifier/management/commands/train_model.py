from django.core.management.base import BaseCommand
from classifier.ml.pipeline import train_model
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Entrena el modelo de clasificación con el conjunto de datos inicial'

    def handle(self, *args, **kwargs):
        try:
            # Verificar que existe el archivo de datos
            data_file = os.path.join(settings.RAW_DATA_DIR, 'bank.csv')
            if not os.path.exists(data_file):
                self.stdout.write(
                    self.style.ERROR(
                        f'No se encontró el archivo bank.csv en {settings.RAW_DATA_DIR}. '
                        f'Por favor, coloque el archivo en esta ubicación.'
                    )
                )
                return

            # Asegurarse de que existe el directorio para el modelo
            os.makedirs(settings.ML_MODEL_DIR, exist_ok=True)

            # Entrenar el modelo
            metrics = train_model(data_file)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Modelo entrenado exitosamente con AUC-ROC: {metrics["auc_roc"]:.4f}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al entrenar el modelo: {str(e)}')
            )