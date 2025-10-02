import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.ml.feature import StringIndexer, VectorAssembler
from .monitor import monitor_performance, log_spark_metrics, update_job_progress
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.sql.functions import col
from pyspark import StorageLevel
import time
from django.utils import timezone
import os
from .monitoring import log_job_status, log_batch_result, log_error


def cleanup_spark_resources(spark, dataframes=None):
    """Limpia los recursos de Spark de manera segura"""
    if dataframes:
        for df in dataframes:
            if df is not None:
                try:
                    df.unpersist()
                except Exception:
                    pass
    
    if spark is not None:
        try:
            spark.stop()
        except Exception:
            pass

def update_job_status(job, status, message=None, progress=None):
    """Actualiza el estado del trabajo y registra el cambio"""
    from django.utils import timezone
    from django.db import transaction
    
    # Refrescar estado desde DB para evitar condiciones de carrera
    job.refresh_from_db()
    
    try:
        with transaction.atomic():
            job.status = status
            if message:
                job.error_message = message
            if progress is not None:
                try:
                    # Si ya conocemos total_records, actualizamos processed_records acorde al porcentaje
                    if getattr(job, 'total_records', 0):
                        pct = min(progress, 100) / 100.0
                        job.processed_records = int(pct * int(job.total_records))
                except Exception as e:
                    log_error(job.id, f"Error al actualizar progreso: {str(e)}", e)
                    pass
            job.save()
        
        # Registrar en el log
        log_job_status(job.id, status, progress, message)
        
    except Exception as e:
        log_error(job.id, f"Error al actualizar estado del job: {str(e)}", e)
        # Intentar loggear en consola como último recurso
        print(f"Error crítico en job {job.id}: {str(e)}")

def process_bank_data(data_path, job):
    """Procesar datos bancarios usando PySpark MLlib
    
    Optimizations applied:
    - Assemble features once and persist the DataFrame
    - Persist indexed DataFrame to avoid recomputes
    - Reuse evaluator across batches
    - Avoid repeated counts where possible
    - Regular status updates
    """
    # Inicializar estado
    update_job_status(job, 'processing', progress=0)
    # Verificar que el archivo de datos existe antes de inicializar Spark
    if not os.path.exists(data_path):
        msg = f"Archivo de datos no encontrado: {data_path}"
        update_job_status(job, 'error', msg)
        job.completed_at = timezone.now()
        job.save()
        return
    # Cerrar conexiones DB antes de inicializar Spark.
    # PySpark/Java puede abrir threads/procesos que no deben compartir conexiones de Django.
    try:
        from django.db import connections
        connections.close_all()
    except Exception:
        pass

    # Environment for Hadoop/Java (user may customize)
    os.environ.setdefault('HADOOP_HOME', r'D:\hadoop')

    # Preferir un JDK 11 instalado localmente para evitar problemas con JDK muy recientes
    # Preferencias: buscar JDK17, luego JDK11 instalados en rutas comunes
    candidates = [
        r'C:\Program Files\BellSoft\LibericaJDK-17',
        r'C:\Program Files\Eclipse Adoptium\jdk-11.0.28+6',
        r'C:\Program Files\Amazon Corretto\jdk11.0.XX',
    ]
    chosen = None
    for cand in candidates:
        if os.path.exists(cand):
            chosen = cand
            break

    if chosen:
        os.environ['JAVA_HOME'] = chosen
        os.environ['PATH'] = os.path.join(chosen, 'bin') + ';' + os.environ.get('PATH', '')
    else:
        # No hay candidato conocido; no sobreescribimos JAVA_HOME existente
        if os.environ.get('JAVA_HOME'):
            os.environ['PATH'] = os.path.join(os.environ['JAVA_HOME'], 'bin') + ';' + os.environ.get('PATH', '')

    # Ensure PySpark uses the venv python if available
    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'venv', 'Scripts', 'python.exe')
    if os.path.exists(venv_python):
        os.environ['PYSPARK_PYTHON'] = venv_python
        os.environ['PYSPARK_DRIVER_PYTHON'] = venv_python

    # Temp dir for Spark
    try:
        os.makedirs(r'D:\spark_tmp', exist_ok=True)
    except Exception:
        pass
    # Antes de inicializar Spark, comprobar versión de Java y HADOOP_HOME en Windows
    import subprocess
    import re

    def _get_java_major():
        try:
            # Preferir el ejecutable de java dentro de JAVA_HOME si está disponible
            java_exe = 'java'
            jhome = os.environ.get('JAVA_HOME')
            if jhome:
                candidate = os.path.join(jhome, 'bin', 'java')
                if os.path.exists(candidate):
                    java_exe = candidate

            p = subprocess.run([java_exe, '-version'], capture_output=True, text=True)
            # java -version normalmente escribe en stderr
            first = (p.stderr or p.stdout).splitlines()[0] if (p.stderr or p.stdout) else ''
            m = re.search(r'"(\d+)(?:\.|$)', first)
            if m:
                return int(m.group(1))
        except Exception:
            return None
        return None

    java_major = _get_java_major()
    # Recomendar JDK 11/17 si detectamos versiones muy recientes (Java 18+ pueden causar incompatibilidades)
    if java_major and java_major >= 18:
        msg = (
            f"Java detectado: {java_major}. Spark/Hadoop en Windows suele funcionar mejor con Java 8/11/17. "
            f"Por favor instale y apunte JAVA_HOME a un JDK compatible (11 o 17) y reinicie el servidor. Current JAVA_HOME={os.environ.get('JAVA_HOME')}"
        )
        job.status = 'error'
        job.error_message = msg
        job.completed_at = timezone.now()
        job.save()
        return

    # En Windows conviene apuntar HADOOP_HOME a una carpeta con winutils.exe
    if os.name == 'nt' and not os.environ.get('HADOOP_HOME'):
        msg = (
            "HADOOP_HOME no configurado. En Windows debes instalar una build de winutils.exe y definir HADOOP_HOME. "
            "Sin esto Spark puede fallar al inicializar. Coloca winutils.exe en %HADOOP_HOME%\\bin y reinicia."
        )
        job.status = 'error'
        job.error_message = msg
        job.completed_at = timezone.now()
        job.save()
        return

    # Initialize Spark with minimal settings optimized for Windows
    # Usar paréntesis para evitar problemas de continuación de línea en Windows
    spark = (
        SparkSession.builder.appName("BankDataProcessor")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.network.timeout", "600s")
        .config("spark.rpc.askTimeout", "300s")
        .config("spark.python.worker.reuse", "false")
        .config("spark.local.dir", r"D:\\spark_tmp")
        .config("spark.driver.host", "localhost")
        .config("spark.driver.bindAddress", "localhost")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .config("spark.scheduler.mode", "FIFO")
        .config("spark.dynamicAllocation.enabled", "false")
        .config("spark.sql.adaptive.enabled", "false")
        .config("spark.cleaner.periodicGC.interval", "30s")
        .config("spark.memory.offHeap.enabled", "false")
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
        .config("spark.io.compression.codec", "lz4")
        .master("local[1]")
        .getOrCreate()
    )
    
    spark.sparkContext.setLogLevel("ERROR")

    df = None
    df_with_idx = None

    try:
        # Leer CSV con schema explícito
        from pyspark.sql.types import StructType, StructField, StringType, IntegerType
        from pyspark.sql.functions import when

        schema = StructType([
            StructField("age", IntegerType(), True),
            StructField("job", StringType(), True),
            StructField("marital", StringType(), True),
            StructField("education", StringType(), True),
            StructField("default", StringType(), True),
            StructField("balance", IntegerType(), True),
            StructField("housing", StringType(), True),
            StructField("loan", StringType(), True),
            StructField("contact", StringType(), True),
            StructField("day", IntegerType(), True),
            StructField("month", StringType(), True),
            StructField("duration", IntegerType(), True),
            StructField("campaign", IntegerType(), True),
            StructField("pdays", IntegerType(), True),
            StructField("previous", IntegerType(), True),
            StructField("poutcome", StringType(), True),
            StructField("y", StringType(), True)
        ])

        # Detectar delimitador
        delim = ','
        try:
            with open(data_path, 'r', encoding='utf-8', errors='ignore') as fh:
                first = fh.readline()
                if ';' in first and first.count(';') > first.count(','):
                    delim = ';'
        except Exception:
            delim = ','

        df = spark.read.option("header", "true").option("delimiter", delim).schema(schema).csv(data_path)

        # Total registros
        update_job_status(job, 'processing', "Contando registros...", 5)
        total_records = df.count()
        job.total_records = total_records
        job.save()

        # Preprocessing
        update_job_status(job, 'processing', "Iniciando preprocesamiento...", 10)
        categorical_columns = ['job', 'marital', 'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
        numeric_columns = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']

        for c in categorical_columns:
            df = df.withColumn(c, col(c).cast('string'))
            df = df.withColumn(c, when(col(c).isNull() | (col(c) == ''), 'missing').otherwise(col(c)))

        for n in numeric_columns:
            df = df.withColumn(n, when(col(n).isNull(), 0).otherwise(col(n)))

        # Indexers
        indexers = [StringIndexer(inputCol=c, outputCol=f"{c}_index", handleInvalid="keep") for c in categorical_columns]
        for idx in indexers:
            df = idx.fit(df).transform(df)

        df = df.fillna({'y': 'no'})
        label_indexer = StringIndexer(inputCol="y", outputCol="label", handleInvalid="keep")
        df = label_indexer.fit(df).transform(df)

        # Features
        update_job_status(job, 'processing', "Preparando características...", 30)
        feature_columns = numeric_columns + [f"{c}_index" for c in categorical_columns]
        assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")
        df = assembler.transform(df)
        df.persist(StorageLevel.MEMORY_AND_DISK)

        # Index for stable batching
        update_job_status(job, 'processing', "Preparando procesamiento por lotes...", 40)
        from pyspark.sql.window import Window
        from pyspark.sql.functions import row_number

        order_col = job.batch_key if job.batch_key in numeric_columns else f"{job.batch_key}_index"
        window = Window.orderBy(order_col)
        df_with_idx = df.withColumn('__row_num', row_number().over(window))
        df_with_idx.persist(StorageLevel.MEMORY_AND_DISK)

        total_batches = (total_records + job.batch_size - 1) // job.batch_size
        evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction")

        for batch_num in range(total_batches):
            # Actualizar progreso (50-95%)
            progress = 50 + (batch_num / total_batches * 45)
            update_job_status(
                job, 
                'processing', 
                f"Procesando lote {batch_num + 1} de {total_batches}...",
                progress
            )
            
            start_idx = batch_num * job.batch_size + 1
            end_idx = min((batch_num + 1) * job.batch_size, total_records)

            batch_df = df_with_idx.filter((col('__row_num') >= start_idx) & (col('__row_num') <= end_idx)).drop('__row_num')

            # Comprobar si el RDD está vacío con reintentos para manejar fallos intermitentes
            is_empty = False
            last_exc = None
            for attempt in range(3):
                try:
                    is_empty = batch_df.rdd.isEmpty()
                    last_exc = None
                    break
                except Exception as e:
                    last_exc = e
                    log_error(job.id, f"Error comprobando isEmpty() en lote {batch_num + 1}: intento {attempt + 1}: {str(e)}", e)
                    # Backoff creciente
                    time.sleep(1 + attempt)

            if last_exc is not None:
                error_msg = f"Error comprobando isEmpty() tras varios intentos: {str(last_exc)}"
                update_job_status(job, 'error', error_msg)
                job.completed_at = timezone.now()
                job.save()
                cleanup_spark_resources(spark, [df, df_with_idx])
                raise RuntimeError(error_msg)

            if is_empty:
                continue

            # Usar configuración más ligera para pruebas y evitar largos tiempos de fit
            rf = RandomForestClassifier(labelCol="label", featuresCol="features", numTrees=3, maxDepth=4)
            start_time = time.time()
            try:
                print(f"Iniciando fit para lote {batch_num + 1}")
                model = rf.fit(batch_df)
                print(f"Fit completado para lote {batch_num + 1}")
            except Exception as fit_err:
                err_msg = str(fit_err)
                if 'Connection reset by peer' in err_msg or 'socket write error' in err_msg:
                    try:
                        model = rf.fit(batch_df)
                    except Exception as retry_err:
                        error_msg = f"Error en reintento para lote {batch_num + 1}/{total_batches}: {str(retry_err)}"
                        job.status = 'error'
                        job.error_message = error_msg
                        job.completed_at = timezone.now()
                        job.save()
                        cleanup_spark_resources(spark, [df, df_with_idx])
                        raise RuntimeError(error_msg) from retry_err
                else:
                    error_msg = f"Error entrenando modelo para lote {batch_num + 1}/{total_batches}: {err_msg}"
                    job.status = 'error'
                    job.error_message = error_msg
                    job.completed_at = timezone.now()
                    job.save()
                    cleanup_spark_resources(spark, [df, df_with_idx])
                    raise RuntimeError(error_msg) from fit_err

            predictions = model.transform(batch_df)

            accuracy = evaluator.evaluate(predictions, {evaluator.metricName: "accuracy"})
            precision = evaluator.evaluate(predictions, {evaluator.metricName: "weightedPrecision"})
            recall = evaluator.evaluate(predictions, {evaluator.metricName: "weightedRecall"})
            f1 = evaluator.evaluate(predictions, {evaluator.metricName: "f1"})

            confusion_matrix = predictions.groupBy("label", "prediction").count().collect()
            conf_matrix_dict = {f"{int(row['label'])}-{int(row['prediction'])}": row['count'] for row in confusion_matrix}

            # Guardar resultados del lote
            try:
                processed = batch_df.count()
                from processor.models import BatchResult
                from django.db import transaction, connections

                # Asegurar que los valores sean válidos
                metrics = {
                    'accuracy': float(accuracy),
                    'precision': float(precision),
                    'recall': float(recall),
                    'f1_score': float(f1),
                }

                # Crear resultado del lote dentro de una transacción.
                # NOTA: no cerrar conexiones dentro de la transacción; cerrar después para asegurar commit.
                with transaction.atomic():
                    BatchResult.objects.create(
                        job=job,
                        batch_number=batch_num + 1,
                        records_processed=processed,
                        accuracy=metrics['accuracy'],
                        precision=metrics['precision'],
                        recall=metrics['recall'],
                        f1_score=metrics['f1_score'],
                        confusion_matrix=conf_matrix_dict,
                        processing_time=time.time() - start_time
                    )

                # Forzar cierre de conexiones y flush tras el commit
                try:
                    connections.close_all()
                except Exception:
                    pass

                # Actualizar progreso total
                job.processed_records += processed
                job.save()

                # Log para debugging
                print(f"Lote {batch_num + 1} completado: {processed} registros, "
                      f"accuracy={metrics['accuracy']:.4f}, "
                      f"tiempo={time.time() - start_time:.2f}s")

            except Exception as save_err:
                error_msg = f"Error guardando resultados del lote {batch_num + 1}: {str(save_err)}"
                update_job_status(job, 'error', error_msg)
                raise RuntimeError(error_msg) from save_err

        # Mark completed
        update_job_status(job, 'completed', "Procesamiento completado", 100)
        job.completed_at = timezone.now()
        job.save()

    except Exception as e:
        error_msg = f"Error en el procesamiento: {str(e)}"
        update_job_status(job, 'error', error_msg)
        job.completed_at = timezone.now()
        job.save()
        raise RuntimeError(error_msg) from e

    finally:
        # Asegurar limpieza de recursos al terminar
        cleanup_spark_resources(spark, [df, df_with_idx])