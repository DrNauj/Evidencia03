import findspark
findspark.init()

from pyspark.sql import SparkSession

def test_spark():
    try:
        # Crear sesión de Spark
        spark = SparkSession.builder \
            .appName("TestConfig") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .config("spark.sql.shuffle.partitions", "2") \
            .getOrCreate()
        
        # Crear un DataFrame de prueba
        test_data = [("test",)]
        df = spark.createDataFrame(test_data, ["col1"])
        
        # Realizar una operación simple
        count = df.count()
        
        print("✅ Configuración de Spark exitosa")
        print(f"Java Home: {spark.sparkContext._jvm.System.getProperty('java.home')}")
        print(f"Spark Version: {spark.version}")
        
        # Limpiar recursos
        spark.stop()
        return True
        
    except Exception as e:
        print("❌ Error en la configuración de Spark:")
        print(str(e))
        return False

if __name__ == "__main__":
    test_spark()