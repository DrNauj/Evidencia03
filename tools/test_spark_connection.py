import findspark
findspark.init()

from pyspark.sql import SparkSession
import os

def test_spark_connection():
    try:
        # Crear sesión de Spark
        spark = SparkSession.builder \
            .appName("TestConnection") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .config("spark.sql.shuffle.partitions", "2") \
            .getOrCreate()
        
        print("✅ Spark inicializado correctamente")
        
        # Probar leer CSV
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'bank.csv')
        if os.path.exists(data_path):
            print(f"✅ Archivo bank.csv encontrado en: {data_path}")
            try:
                df = spark.read.csv(data_path, header=True, inferSchema=True)
                count = df.count()
                print(f"✅ CSV leído correctamente - {count} registros encontrados")
                print("\nPrimeras 5 filas:")
                df.show(5)
            except Exception as e:
                print(f"❌ Error al leer CSV: {str(e)}")
        else:
            print(f"❌ No se encuentra bank.csv en: {data_path}")
        
        # Limpiar
        spark.stop()
        return True
    except Exception as e:
        print(f"❌ Error al inicializar Spark: {str(e)}")
        return False

if __name__ == "__main__":
    test_spark_connection()