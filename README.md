# Evidencia 3: Procesamiento por Lotes con PySpark MLlib y Django

Aplicación web que procesa un CSV en lotes usando PySpark (local) y muestra métricas por lote en una interfaz Django.

## Estructura mínima del proyecto

```
Evidencia03/
├── data/                  # Directorio para datasets (poner aquí bank.csv)
├── bankprocessor/         # Proyecto Django (contiene manage.py)
│   └── processor/         # App principal
├── requirements.txt       # Dependencias Python
└── README.md
```

## Requisitos

- Python 3.9 (probado con 3.9.13)
- Java JDK 11+ para PySpark (OpenJDK funciona)
- Virtualenv / venv

Nota: en Windows, PySpark puede requerir `winutils.exe` para operaciones HDFS temporales; en entornos locales suele funcionar con la configuración incluida en el proyecto.

## Instalación rápida (Windows PowerShell)

1. Crear/activar entorno virtual

```powershell
cd "D:\ruta\a\Evidencia03"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Instalar dependencias

```powershell
pip install -r requirements.txt
```

3. Preparar datos

- Copia `bank.csv` a la carpeta `data/` del proyecto raíz.

4. Migraciones y servidor

```powershell
cd bankprocessor
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py runserver
```

Abre http://localhost:8000/ para usar la interfaz.

## Cómo ejecutar un job

- Desde la UI: completar el formulario en la página de inicio y pulsar "Procesar". La vista lanza un proceso hijo que ejecuta el management command `run_job`.
- Desde terminal (útil para debug):

```powershell
cd bankprocessor
venv\Scripts\python.exe manage.py run_job <job_id>
```

Logs por job: cuando se lanza desde la UI se crea `job_logs/run_job_<id>.log` en la carpeta que contiene `manage.py` (por ejemplo `bankprocessor/job_logs/run_job_81.log`). Si un job no avanza, revisa ese fichero primero.

## Gráficos en la página de resultados

- Se incorporó Chart.js (desde CDN) en la plantilla `processor/templates/processor/results.html`.
- Gráficos implementados:
  - Línea: Accuracy por lote (0..1)
  - Barras: Registros procesados por lote
- Ambos gráficos se actualizan automáticamente usando la API JSON existente (`/api/results/?job_id=<id>`). No se cambió la API del backend.

Cómo desactivar los gráficos rápidamente:

1. Edita `processor/templates/processor/results.html` y comenta o elimina la inclusión del CDN:

```html
<!-- <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script> -->
```

2. Comenta el bloque JS que inicializa/actualiza los charts (al final de la plantilla) o restaura la plantilla original desde control de versiones.

## Buenas prácticas y notas

- Evita ejecutar PySpark desde el mismo proceso que corre Django (esto provoca conflictos con SparkContext); por eso el proyecto lanza `manage.py run_job` en un proceso hijo.
- Si planeas ejecutar jobs largos en producción, usar un broker (Celery + Redis) o un job runner es preferible. En este proyecto Celery fue eliminado para evitar complejidad innecesaria.
- Si trabajas con datasets mucho más grandes, considera agrupar lotes en la gráfica o paginar/mostrar sólo los últimos N lotes para mantener la UI responsiva.

## Contribuir

1. Crear rama: `git checkout -b feature/nombre`
2. Hacer commits claros y atómicos
3. Push y abrir PR

---