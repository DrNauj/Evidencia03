from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml import Pipeline
from pyspark.ml.pipeline import PipelineModel
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import os
import json
from datetime import datetime
from django.conf import settings

def create_spark_session():
    """Crear y configurar una sesión de Spark con la memoria especificada."""
    # Configurar Spark con Hadoop en Windows
    import os
    os.environ['HADOOP_HOME'] = os.path.join(settings.BASE_DIR, 'data', 'hadoop')
    os.environ['PATH'] = os.path.join(os.environ['HADOOP_HOME'], 'bin') + os.pathsep + os.environ['PATH']
    
    builder = SparkSession.builder \
        .appName("BankCustomerClassifier") \
        .config("spark.executor.memory", "2g") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.warehouse.dir", "spark-warehouse")
    
    # Configuración local
    builder = builder.master("local[*]")
    
    return builder.getOrCreate()

def load_data(spark, file_path):
    """Cargar y preparar el conjunto de datos."""
    # Cargar el CSV
    df = spark.read.csv(file_path, header=True, inferSchema=True)
    
    # Convertir explícitamente 'deposit' a valores binarios
    df = df.withColumn("deposit", 
                      F.when(F.col("deposit") == "yes", 1.0)
                       .otherwise(0.0))
    
    # Definir columnas categóricas y numéricas
    categorical_cols = ['job', 'marital', 'education', 'default', 'housing', 
                       'loan', 'contact', 'month', 'poutcome']
    numeric_cols = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']
    
    # Crear indexadores para variables categóricas
    indexers = []
    oh_encoders = []
    
    for col in categorical_cols:
        # Crear indexador
        indexer = StringIndexer(inputCol=col, outputCol=f"{col}_index", handleInvalid="keep")
        indexers.append(indexer)
        
        # Crear codificador one-hot
        encoder = OneHotEncoder(inputCol=f"{col}_index", outputCol=f"{col}_vec", dropLast=True)
        oh_encoders.append(encoder)
    
    # Preparar el ensamblador de características
    feature_cols = [f"{col}_vec" for col in categorical_cols] + numeric_cols
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
    
    # No necesitamos indexar la etiqueta ya que la convertimos explícitamente a binaria
    label_indexer = None
    
    return df, indexers, oh_encoders, assembler, label_indexer

def create_pipeline(indexers, oh_encoders, assembler):
    """Crear el pipeline de ML con Random Forest."""
    rf = RandomForestClassifier(
        labelCol="deposit",  # Usar deposit directamente como etiqueta
        featuresCol="features",
        numTrees=100,
        maxDepth=5,
        seed=42
    )
    
    # Construir el pipeline completo
    pipeline_stages = indexers + oh_encoders + [assembler, rf]
    pipeline = Pipeline(stages=pipeline_stages)
    
    return pipeline, rf

def save_metrics(metrics, model_dir):
    """Guardar las métricas del modelo para el dashboard."""
    metrics_file = os.path.join(model_dir, "model_metrics.json")
    metrics["timestamp"] = datetime.now().isoformat()
    
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=4)

def train_model(file_path, model_dir=None):
    """Entrenar el modelo usando validación cruzada y guardarlo."""
    if model_dir is None:
        model_dir = os.path.join(settings.ML_MODEL_DIR, "bank_customer_model")
    
    spark = create_spark_session()
    
    try:
        # Cargar y preparar datos
        df, indexers, oh_encoders, assembler, _ = load_data(spark, file_path)
        
        pipeline, rf = create_pipeline(indexers, oh_encoders, assembler)
        
        # Configurar validación cruzada
        paramGrid = ParamGridBuilder() \
            .addGrid(rf.numTrees, [50, 100]) \
            .addGrid(rf.maxDepth, [5, 10]) \
            .build()
        
        evaluator = BinaryClassificationEvaluator(
            labelCol="deposit",
            metricName="areaUnderROC"
        )
        
        crossval = CrossValidator(
            estimator=pipeline,
            estimatorParamMaps=paramGrid,
            evaluator=evaluator,
            numFolds=5,
            seed=42
        )
        
        # Dividir datos
        train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)
        
        # Entrenar modelo con validación cruzada
        cv_model = crossval.fit(train_df)
        
        # Evaluar en conjunto de prueba
        predictions = cv_model.transform(test_df)
        auc_roc = float(evaluator.evaluate(predictions))
        
        # Obtener el mejor modelo
        best_model = cv_model.bestModel
        
        # Guardar el mejor modelo usando formato nativo de Spark
        model_path = os.path.join(model_dir, "model")
        best_model.write().overwrite().save(model_path)
        
        # Guardar métricas
        metrics = {
            "auc_roc": auc_roc,
            "best_params": {}
        }
        
        # Intentar obtener parámetros del modelo de forma segura
        try:
            rf_model = best_model.stages[-1]
            metrics["best_params"]["numTrees"] = rf_model.getNumTrees()
            metrics["best_params"]["maxDepth"] = rf_model.getMaxDepth()
        except:
            # Si no podemos obtener los parámetros, usar valores por defecto
            metrics["best_params"]["numTrees"] = 100
            metrics["best_params"]["maxDepth"] = 5
        
        # Intentar obtener métricas de validación cruzada si están disponibles
        try:
            avg_metrics = [float(m) for m in cv_model.avgMetrics]
            metrics["cross_validation_metrics"] = {
                "avg_metric": sum(avg_metrics) / len(avg_metrics),
                "metrics": avg_metrics
            }
        except:
            pass  # Si no hay métricas de CV, omitirlas
            
        save_metrics(metrics, model_dir)
        
        return metrics
        
    finally:
        spark.stop()

def load_model_and_predict(spark, data):
    """Cargar el modelo guardado y realizar predicciones."""
    model_dir = os.path.join(settings.ML_MODEL_DIR, "bank_customer_model")
    
    if not os.path.exists(model_dir):
        raise Exception("El modelo no existe. Por favor, entrene el modelo primero.")
    
    # Cargar el modelo
    model_path = os.path.join(model_dir, "model")
    model = PipelineModel.load(model_path)
    
    # Realizar predicciones
    predictions = model.transform(data)
    
    return predictions

if __name__ == "__main__":
    # Ejemplo de uso
    file_path = os.path.join(settings.RAW_DATA_DIR, "bank.csv")
    metrics = train_model(file_path)
    print(f"Métricas del modelo: {json.dumps(metrics, indent=2)}")