import findspark
findspark.init()
from pyspark.sql import SparkSession
import os
print('Python executable:', os.path.realpath(os.sys.executable))
print('Python version:', os.sys.version)

spark = SparkSession.builder.master('local[1]').appName('worker_test')\
    .config('spark.python.worker.reuse', 'false')\
    .config('spark.driver.host', 'localhost')\
    .config('spark.driver.bindAddress', 'localhost')\
    .getOrCreate()

sc = spark.sparkContext
sc.setLogLevel('ERROR')

r = sc.parallelize(list(range(1000)))
print('Starting collect()')
res = r.map(lambda x: x+1).collect()
print('Collect done, len=', len(res))
spark.stop()
