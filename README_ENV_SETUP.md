# Configurar entorno para ejecutar PySpark en Windows

Resumen rápido:

- PySpark (Spark) en Windows necesita un JDK compatible (recomendado JDK 11 o 17). Java muy recientes (18+) pueden causar errores como "getSubject is supported only if a security manager is allowed".
- Para ejecutar Spark local en Windows necesitarás `winutils.exe` (colocado en %HADOOP_HOME%\bin) y definir `HADOOP_HOME`.

Pasos recomendados:

1. Instalar JDK 11 o 17
   - Descargar e instalar Liberica/OpenJDK 11 o 17.
   - Establecer la variable de entorno `JAVA_HOME` apuntando a la carpeta del JDK (por ejemplo: `C:\Program Files\BellSoft\LibericaJDK-17`).
   - Añadir `%JAVA_HOME%\bin` al `PATH`.

2. Instalar winutils.exe (opcional pero recomendado en Windows)
   - Descargar una build de winutils adecuada para la versión de Hadoop usada por tu Spark (p. ej. buscar "winutils.exe hadoop 2.7" en GitHub builds).
   - Crear `C:\hadoop\bin` y colocar `winutils.exe` ahí.
   - Establecer `HADOOP_HOME=C:\hadoop` y añadir `%HADOOP_HOME%\bin` al `PATH`.

3. Reiniciar PowerShell/Windows para que las variables de entorno estén disponibles en nuevos procesos.

4. Verificar desde el venv del proyecto:

```powershell
# activar venv (si no activado)
& .\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python bankprocessor\tools\check_env.py
```

Si `check_env.py` muestra Java version >= 18 o que `HADOOP_HOME` no está definido, sigue las instrucciones anteriores.

## Configuración Optimizada de Spark

La aplicación usa una configuración optimizada de Spark para procesar datos en lotes:

```python
SparkSession.builder \
    .appName("BankDataProcessor") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "4") \
    .config("spark.memory.offHeap.enabled", "true") \
    .config("spark.memory.offHeap.size", "2g") \
    .master("local[2]")
```

Si experimentas problemas de memoria o rendimiento, puedes ajustar:

- `spark.driver.memory`: Memoria para el proceso driver (2g por defecto)
- `spark.executor.memory`: Memoria para los ejecutores (2g por defecto)
- `spark.sql.shuffle.partitions`: Número de particiones para operaciones shuffle (4 por defecto)
- `spark.memory.offHeap.size`: Memoria fuera del heap de Java (2g por defecto)

## Solución de Problemas Comunes

### 1. Error "Java Gateway process exited"
- **Causa**: Java incompatible o no encontrado
- **Solución**: 
  - Verifica que JAVA_HOME apunta a JDK 11 o 17
  - Asegúrate que java.exe está en el PATH
  - Reinicia el servidor Django

### 2. Error "Failed to locate the winutils binary"
- **Causa**: Configuración de Hadoop incorrecta en Windows
- **Solución**:
  - Verifica HADOOP_HOME (debe apuntar a la carpeta que contiene bin/winutils.exe)
  - Reinstala winutils.exe si es necesario

### 3. Error "SparkContext already exists"
- **Causa**: Múltiples intentos de crear SparkContext
- **Solución**: 
  - La aplicación maneja esto automáticamente con limpieza de recursos
  - Si persiste, reinicia el servidor Django

### 4. Errores de Memoria
- **Causa**: Recursos insuficientes o mala gestión
- **Solución**:
  - Reduce el tamaño de lote en la configuración
  - Ajusta spark.driver.memory y spark.executor.memory
  - Verifica que no hay otros procesos consumiendo mucha memoria

Alternativa: usar WSL2 o Docker

- Para desarrollo en PySpark recomiendo usar WSL2 o Docker: Spark y su integración con Python suelen ser mucho más estables en Linux.
- Si quieres, puedo añadir un `Dockerfile` y `docker-compose.yml` para levantar un contenedor que ejecute Django + Spark en un entorno controlado.
