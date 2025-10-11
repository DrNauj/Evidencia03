import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pyspark.sql import SparkSession
from django.conf import settings
from .pipeline import load_model_and_predict

class FileHandler(FileSystemEventHandler):
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("BankCustomerStreamProcessor") \
            .config("spark.executor.memory", "2g") \
            .getOrCreate()

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.csv'):
            self.process_file(event.src_path)

    def process_file(self, file_path):
        try:
            # Cargar nuevo archivo CSV
            df = self.spark.read.csv(file_path, header=True, inferSchema=True)
            
            # Realizar predicciones
            predictions = load_model_and_predict(self.spark, df)
            
            # Guardar resultados
            output_path = os.path.join(
                settings.PROCESSED_DATA_DIR,
                f"processed_{os.path.basename(file_path)}"
            )
            
            # Seleccionar solo las columnas relevantes
            predictions = predictions.select(
                "*",
                predictions["prediction"].cast("int").alias("predicted_deposit")
            )
            
            # Guardar como CSV
            predictions.write.csv(output_path, header=True, mode="overwrite")
            
            print(f"Archivo procesado: {file_path}")
            print(f"Resultados guardados en: {output_path}")
            
        except Exception as e:
            print(f"Error procesando archivo {file_path}: {str(e)}")

class StreamProcessor:
    def __init__(self, watch_directory=None):
        self.watch_directory = watch_directory or settings.RAW_DATA_DIR
        self.event_handler = FileHandler()
        self.observer = Observer()

    def start(self):
        """Iniciar la vigilancia del directorio."""
        self.observer.schedule(self.event_handler, self.watch_directory, recursive=False)
        self.observer.start()
        print(f"Vigilando directorio: {self.watch_directory}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
            print("\nVigilancia detenida")
        
        self.observer.join()

    def stop(self):
        """Detener la vigilancia del directorio."""
        self.observer.stop()
        self.observer.join()
        print("Vigilancia detenida")