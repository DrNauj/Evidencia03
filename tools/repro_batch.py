import findspark
findspark.init()
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import os

print('Python executable:', os.path.realpath(os.sys.executable))

spark = SparkSession.builder.master('local[1]').appName('repro_batch')\
    .config('spark.python.worker.reuse', 'false')\
    .config('spark.driver.host', 'localhost')\
    .config('spark.driver.bindAddress', 'localhost')\
    .config('spark.sql.session.timeZone','UTC')\
    .getOrCreate()

sc = spark.sparkContext
sc.setLogLevel('ERROR')

data_path = r"D:\Proyectos python\Evidencia03\bankprocessor\data\bank.csv"

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

print('Reading CSV...')
df = spark.read.option('header','true').schema(schema).csv(data_path)
print('Count rows...')
print(df.count())

# minimal preprocessing
numeric_columns = ['age', 'balance', 'day', 'duration', 'campaign', 'pdays', 'previous']
for n in numeric_columns:
    df = df.withColumn(n, when(col(n).isNull(), 0).otherwise(col(n)))

from pyspark.ml.feature import StringIndexer, VectorAssembler
categorical_columns = ['job', 'marital', 'education', 'default', 'housing', 'loan', 'contact', 'month', 'poutcome']
for c in categorical_columns:
    df = df.withColumn(c, col(c).cast('string'))
    df = df.withColumn(c, when(col(c).isNull() | (col(c) == ''), 'missing').otherwise(col(c)))

indexers = [StringIndexer(inputCol=c, outputCol=f"{c}_index", handleInvalid="keep") for c in categorical_columns]
for idx in indexers:
    df = idx.fit(df).transform(df)

label_indexer = StringIndexer(inputCol='y', outputCol='label', handleInvalid='keep')
df = label_indexer.fit(df).transform(df)

feature_columns = numeric_columns + [f"{c}_index" for c in categorical_columns]
assembler = VectorAssembler(inputCols=feature_columns, outputCol='features')
df = assembler.transform(df)

df.persist()
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

window = Window.orderBy('age')
df_with_idx = df.withColumn('__row_num', row_number().over(window))
df_with_idx.persist()

# pick a small batch
start_idx = 1
end_idx = 100
batch_df = df_with_idx.filter((col('__row_num') >= start_idx) & (col('__row_num') <= end_idx)).drop('__row_num')
print('Checking batch_df.rdd.isEmpty()')
print(batch_df.rdd.isEmpty())
print('Counting batch')
print(batch_df.count())

print('Trying to train a small RandomForest (numTrees=1)')
from pyspark.ml.classification import RandomForestClassifier
rf = RandomForestClassifier(labelCol='label', featuresCol='features', numTrees=1, maxDepth=3)
model = rf.fit(batch_df)
print('Model trained OK')

spark.stop()
