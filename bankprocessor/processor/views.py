from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .forms import ProcessingConfigForm
from .models import ProcessingJob, BatchResult
import os
import pandas as pd
import threading

def home(request):
    """Vista principal con formulario de configuración"""
    if request.method == 'POST':
        form = ProcessingConfigForm(request.POST)
        if form.is_valid():
            # Evitar crear jobs duplicados: si ya existe uno pending/processing, redirigimos a sus resultados
            existing = ProcessingJob.objects.filter(status__in=['pending', 'processing']).order_by('-started_at').first()
            if existing:
                messages.info(request, 'Ya existe un trabajo en curso. Mostrando resultados del trabajo actual.')
                return redirect('view_results_job', job_id=existing.id)

            # Crear nuevo job de procesamiento
            job = ProcessingJob.objects.create(
                batch_key=form.cleaned_data['batch_key'],
                batch_size=form.cleaned_data['batch_size']
            )
            messages.success(request, 'Procesamiento creado. Iniciando...')
            return redirect('process_data')
    else:
        form = ProcessingConfigForm()
    
    # Obtener estado del último job
    latest_job = ProcessingJob.objects.first()
    
    return render(request, 'processor/home.html', {
        'title': 'Bank Data Processor',
        'form': form,
        'latest_job': latest_job
    })

def process_data(request):
    """Procesar datos por lotes usando PySpark"""
    from .ml_processor import process_bank_data

    # Obtener el último job pendiente
    job = ProcessingJob.objects.filter(status='pending').first()

    if not job:
        messages.warning(request, 'No hay trabajos pendientes')
        return redirect('home')

    # Verificar existencia del archivo
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'bank.csv')
    if not os.path.exists(data_path):
        messages.error(request, 'No se encuentra el archivo bank.csv en la carpeta data/')
        return redirect('home')

    # Actualizar estado y lanzar procesamiento en un proceso separado para aislar Spark
    job.status = 'processing'
    job.processed_records = 0
    job.error_message = ''
    job.save()

    # Lanzar el comando de management en un proceso externo para evitar múltiples SparkContext
    import subprocess, sys
    # Buscar manage.py ascendiendo desde este archivo (soporta distintas estructuras)
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    manage_py = None
    for _ in range(4):
        candidate = os.path.join(cur_dir, 'manage.py')
        if os.path.exists(candidate):
            manage_py = os.path.abspath(candidate)
            break
        cur_dir = os.path.abspath(os.path.join(cur_dir, '..'))

    # Fallback razonable: si no encontramos manage.py, usar el par de niveles anterior (compatibilidad)
    if manage_py is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        manage_py = os.path.abspath(os.path.join(project_root, 'manage.py'))
    # El directorio raíz del proyecto donde está manage.py
    project_root = os.path.dirname(manage_py)

    # Detectar python del virtualenv buscando en ubicaciones habituales
    venv_candidates = [
        os.path.join(project_root, 'venv', 'Scripts', 'python.exe'),
        os.path.join(os.path.dirname(project_root), 'venv', 'Scripts', 'python.exe'),
        os.path.join(project_root, '..', 'venv', 'Scripts', 'python.exe')
    ]
    python_exe = sys.executable
    for p in venv_candidates:
        p_abs = os.path.abspath(p)
        if os.path.exists(p_abs):
            python_exe = p_abs
            break

    # Preparar logfile para el proceso hijo (en la misma carpeta de manage.py)
    # place per-job logs inside a dedicated folder to keep project root tidy
    logs_dir = os.path.join(project_root, 'job_logs')
    os.makedirs(logs_dir, exist_ok=True)
    logfile = os.path.join(logs_dir, f'run_job_{job.id}.log')
    try:
        with open(logfile, 'ab') as out:
            # Usar Popen sin esperar; redirigir stdout/stderr a logfile
            subprocess.Popen([python_exe, manage_py, 'run_job', str(job.id)], cwd=project_root, stdout=out, stderr=out)
    except Exception as e:
        # Si no podemos lanzar el proceso, marcar job como error
        job.status = 'error'
        job.error_message = f'Failed to spawn worker process: {e}'
        job.save()

    messages.success(request, 'Procesamiento en segundo plano iniciado. Visualizando resultados...')
    # Redirigir a la página de resultados específica del job para que el template reciba job_id
    return redirect('view_results_job', job_id=job.id)

def view_results(request, job_id=None):
    """Mostrar resultados del procesamiento

    Acepta opcionalmente job_id desde la URL (path parameter) o lo toma del resolver.
    """
    # Permitir ver resultados de un job específico usando job_id en la URL o como parámetro opcional
    if job_id is None:
        # intentar obtener desde resolver_match para compatibilidad con llamadas previas
        job_id = request.resolver_match.kwargs.get('job_id') if request.resolver_match else None
    
    # Asegurarse de que job_id_js esté disponible para el JavaScript

    if job_id:
        job = ProcessingJob.objects.filter(id=job_id).first()
    else:
        # Seleccionamos el job más reciente (por fecha de inicio) si no se especifica job_id
        job = ProcessingJob.objects.filter(status__in=['completed', 'processing', 'pending']).order_by('-started_at').first()

    # Si no hay job activo/completado en primera instancia, no hacemos return temprano;
    # renderizamos la página y dejamos que el JS consulte el último job disponible.
    if not job:
        results = BatchResult.objects.none()
        latest_job = ProcessingJob.objects.first()
        job_id_js = latest_job.id if latest_job else 'null'
    else:
        results = BatchResult.objects.filter(job=job)
        job_id_js = job.id

    return render(request, 'processor/results.html', {
        'job': job,
        'results': results,
        'job_id_js': job_id_js,
    })

def job_history(request):
    """Listar historial de ProcessingJob"""
    # Soporta order_by y sort por query params (ej: ?order_by=started_at&sort=asc)
    order_by = request.GET.get('order_by', 'started_at')
    sort = request.GET.get('sort', 'desc')
    if sort == 'asc':
        jobs = ProcessingJob.objects.all().order_by(order_by)
    else:
        jobs = ProcessingJob.objects.all().order_by('-' + order_by)
    # preparar flags para la plantilla (evitar comparaciones complejas en el template)
    ctx = {
        'jobs': jobs,
        'order_by': order_by,
        'sort': sort,
        'order_started': order_by == 'started_at',
        'order_progress': order_by == 'progress',
        'order_batch_size': order_by == 'batch_size',
        'sort_asc': sort == 'asc',
    }
    return render(request, 'processor/history.html', ctx)


def job_delete(request, job_id):
    if request.method == 'POST':
        ProcessingJob.objects.filter(id=job_id).delete()
        messages.success(request, f'Job {job_id} eliminado')
    return redirect('job_history')


def job_terminate(request, job_id):
    # Forzar estado error/terminated para un job en processing
    if request.method == 'POST':
        job = ProcessingJob.objects.filter(id=job_id).first()
        if job and job.status == 'processing':
            job.status = 'error'
            job.error_message = 'Terminado manualmente por el usuario'
            job.save()
            messages.success(request, f'Job {job_id} terminado')
    return redirect('job_history')


def job_resume(request, job_id):
    # Reanudar un job que quedó en 'error' o 'pending' marcándolo como 'pending' y dejando que /process/ lo recoja
    if request.method == 'POST':
        job = ProcessingJob.objects.filter(id=job_id).first()
        if job and job.status in ['error', 'pending']:
            job.status = 'pending'
            job.error_message = ''
            job.save()
            messages.success(request, f'Job {job_id} reanudado (pendiente)')
    return redirect('job_history')


def job_clear_history(request):
    # Eliminar jobs completados o en error
    if request.method == 'POST':
        ProcessingJob.objects.filter(status__in=['completed', 'error']).delete()
        messages.success(request, 'Historial limpiado (jobs completed/error eliminados)')
    return redirect('job_history')

def processing_status(request):
    """API endpoint para consultar estado del procesamiento"""
    # Permitir consulta por job_id como query param ?job_id=NN
    job_id = request.GET.get('job_id')
    if job_id:
        job = ProcessingJob.objects.filter(id=job_id).first()
    else:
        job = ProcessingJob.objects.first()

    if not job:
        return JsonResponse({
            'status': 'no_jobs',
            'progress': 0,
            'processed_records': 0,
            'total_records': 0,
            'results_count': 0,
            'message': 'No hay trabajos de procesamiento'
        })

    # Obtener los resultados por lotes
    batch_results = BatchResult.objects.filter(job=job).order_by('batch_number')
    results = []
    
    # Métricas agregadas
    avg = {
        'accuracy': 0,
        'precision': 0,
        'recall': 0,
        'f1_score': 0
    }
    
    # Procesar resultados
    for r in batch_results:
        result_data = {
            'batch_number': r.batch_number,
            'records_processed': r.records_processed,
            'accuracy': r.accuracy,
            'precision': r.precision,
            'recall': r.recall,
            'f1_score': r.f1_score,
            'processing_time': r.processing_time
        }
        results.append(result_data)
        
        # Acumular métricas
        avg['accuracy'] += r.accuracy
        avg['precision'] += r.precision
        avg['recall'] += r.recall
        avg['f1_score'] += r.f1_score
    
    # Calcular promedios si hay resultados
    results_count = len(results)
    if results_count > 0:
        for key in avg:
            avg[key] /= results_count

    return JsonResponse({
        'job_id': job.id,
        'status': job.status,
        'progress': job.progress,
        'processed_records': job.processed_records,
        'total_records': job.total_records,
        'results_count': results_count,
        'message': job.error_message if job.status == 'error' else None,
        'results': results,
        'averages': avg
    })

def processing_results_json(request):
    """Devuelve resultados por lote y métricas agregadas en JSON para un job dado (query param job_id)."""
    job_id = request.GET.get('job_id')
    if job_id:
        job = ProcessingJob.objects.filter(id=job_id).first()
    else:
        job = ProcessingJob.objects.first()

    if not job:
        return JsonResponse({'error': 'no_jobs'}, status=404)

    results_qs = BatchResult.objects.filter(job=job).order_by('batch_number')
    results = []
    for r in results_qs:
        results.append({
            'batch_number': r.batch_number,
            'records_processed': r.records_processed,
            'accuracy': r.accuracy,
            'precision': r.precision,
            'recall': r.recall,
            'f1_score': r.f1_score,
            'processing_time': r.processing_time
        })

    # métricas agregadas simples (media)
    avg = {
        'accuracy': None,
        'precision': None,
        'recall': None,
        'f1_score': None
    }
    if results:
        avg['accuracy'] = sum(r['accuracy'] for r in results) / len(results)
        avg['precision'] = sum(r['precision'] for r in results) / len(results)
        avg['recall'] = sum(r['recall'] for r in results) / len(results)
        avg['f1_score'] = sum(r['f1_score'] for r in results) / len(results)

    return JsonResponse({
        'job_id': job.id,
        'status': job.status,
        'progress': job.progress,
        'processed_records': job.processed_records,
        'total_records': job.total_records,
        'results_count': len(results),
        'results': results,
        'averages': avg,
        'message': job.error_message if job.status == 'error' else None
    })
