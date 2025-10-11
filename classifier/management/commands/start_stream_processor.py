from django.core.management.base import BaseCommand
from classifier.ml.stream_processor import StreamProcessor
import time

class Command(BaseCommand):
    help = 'Inicia el procesador de streaming para nuevos archivos CSV'

    def handle(self, *args, **kwargs):
        try:
            processor = StreamProcessor()
            processor.start()

            self.stdout.write(
                self.style.SUCCESS('Procesador de streaming iniciado. '
                                'Presiona Ctrl+C para detener.')
            )

            # Mantener el proceso ejecutándose
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                processor.stop()
                self.stdout.write(
                    self.style.SUCCESS('Procesador de streaming detenido.')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al iniciar el procesador: {str(e)}')
            )