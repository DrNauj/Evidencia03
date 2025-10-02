import os
# Forzar JAVA_HOME y HADOOP_HOME antes de cargar PySpark/JVM
os.environ['JAVA_HOME'] = r'C:\Program Files\Eclipse Adoptium\jdk-8.0.462.8-hotspot'
os.environ['HADOOP_HOME'] = r'D:\hadoop'
os.environ['PATH'] = os.path.join(os.environ['JAVA_HOME'], 'bin') + ';' + os.environ.get('PATH', '')

import findspark
findspark.init()
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when

spark = SparkSession.builder.master('local[2]').appName('test_spark').getOrCreate()
print('Spark iniciado:', spark)

schema = None
csv_path = r'd:\Proyectos python\Evidencia03\data\bank.csv'

# Detectar delimiter leyendo la primera line del archivo localmente
delim = ','
with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
    first = f.readline()
    if ';' in first and first.count(';') > first.count(','):
        delim = ';'

# Leer sin esquema para pruebas rápidas
df = spark.read.option('header', 'true').option('delimiter', delim).csv(csv_path)
print('Total rows:', df.count())
print('Columns:', df.columns)
print('Primeras 5 filas:')
df.show(5, truncate=False)

categorical_columns = ['job', 'marital', 'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
numeric_columns = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']

# Mostrar conteo de nulos y empty antes
print('\nAntes del fill:')
for c in categorical_columns:
    n = df.filter((col(c).isNull()) | (col(c) == '')).count()
    print(f"{c}: {n}")

# Aplicar relleno como en ml_processor
for c in categorical_columns:
    df = df.withColumn(c, col(c).cast('string'))
    df = df.withColumn(c, when(col(c).isNull() | (col(c) == ''), 'missing').otherwise(col(c)))
for n in numeric_columns:
    df = df.withColumn(n, when(col(n).isNull(), 0).otherwise(col(n)))

# Mostrar conteo de nulos y empty después
print('\nDespués del fill:')
for c in categorical_columns:
    n = df.filter((col(c).isNull()) | (col(c) == '')).count()
    print(f"{c}: {n}")

# Probar StringIndexer fit para una columna
from pyspark.ml.feature import StringIndexer
si = StringIndexer(inputCol='job', outputCol='job_index', handleInvalid='keep')
model = si.fit(df)
df2 = model.transform(df)
print('\nEjemplo job_index distinct count:', df2.select('job_index').distinct().count())

spark.stop()
print('Fin prueba')