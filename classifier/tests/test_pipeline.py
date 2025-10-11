import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bankprocessor.settings')
django.setup()

from classifier.ml.pipeline import train_model
from django.conf import settings

def test_pipeline():
    """Probar el pipeline de ML completo."""
    print("Iniciando prueba del pipeline ML...")
    
    try:
        # Entrenar modelo
        file_path = os.path.join(settings.RAW_DATA_DIR, "bank.csv")
        print(f"Entrenando modelo con datos de: {file_path}")
        
        metrics = train_model(file_path)
        
        print("\nEntrenamiento exitoso!")
        print("\nMétricas del modelo:")
        print(f"AUC-ROC: {metrics['auc_roc']:.4f}")
        print("\nMejores parámetros:")
        print(f"Número de árboles: {metrics['best_params']['numTrees']}")
        print(f"Profundidad máxima: {metrics['best_params']['maxDepth']}")
        print("\nMétricas de validación cruzada:")
        print(f"Promedio: {metrics['cross_validation_metrics']['avg_metric']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"\nError durante la prueba: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)