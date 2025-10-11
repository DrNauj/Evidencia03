# **DOCUMENTACIÓN TÉCNICA Y ESTRATÉGICA**

## **Sistema de Clasificación de Suscripción Bancaria en Tiempo Real**

**Proyecto Educativo: Integración End-to-End de ML y Spark Streaming**

## **1\. INTRODUCCIÓN Y ALCANCE ESTRATÉGICO**

### **1.1. Propósito y Justificación Educativa**

Este proyecto tiene como objetivo principal servir como una **demostración práctica y funcional** de la integración de un modelo de Machine Learning entrenado (utilizando **PySpark MLlib**) con una arquitectura de procesamiento de datos en tiempo real (**Spark Streaming**), todo orquestado a través de una aplicación web (**Django**).

El enfoque educativo es crear un sistema **end-to-end** que simule un entorno industrial real, cubriendo desde la ingesta de datos hasta la toma de decisiones del usuario final.

### **1.2. Contexto de Negocio: Depósitos a Plazo Fijo**

El modelo de negocio se centra en predecir la **propensión de un cliente a suscribir un Depósito a Plazo Fijo**.

| Parte | Beneficio Clave |
| :---- | :---- |
| **Banco** | Obtiene fondos estables para operaciones crediticias, optimiza campañas de marketing y fideliza clientes. |
| **Cliente** | Mayor rentabilidad garantizada sobre sus ahorros y planificación financiera predecible. |

### **1.3. Perfiles de Usuario del Sistema**

El sistema está diseñado para ser utilizado principalmente por el **Agente de Banco**, quien necesita:

1. **Predicción Individual:** Obtener un resultado inmediato para un cliente atendido en el momento (vía formulario web).  
2. **Análisis por Lotes:** Procesar grandes bases de datos de clientes para campañas de marketing (vía carga de archivo CSV).  
3. **Monitoreo:** Observar el progreso y los resultados agregados en tiempo real a través del Dashboard.

## **2\. ARQUITECTURA DEL SISTEMA Y FLUJO OPERACIONAL**

### **2.1. Componentes Principales y Stack Tecnológico**

La arquitectura se basa en una capa de presentación (Django), una capa de persistencia mínima (SQLite para Django, File System para datos), y la capa de procesamiento (PySpark).

| Componente | Tecnología | Función Específica |
| :---- | :---- | :---- |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla) | Interfaz de usuario, Polling para resultados, Carga de archivos. |
| **Backend Web** | Django (Python) | Generación de archivos JSON de entrada, Enrutamiento, Presentación de resultados. |
| **Machine Learning** | PySpark MLlib (Random Forest) | Entrenamiento y guardado del modelo, Inferencia en el micro-batch. |
| **Streaming** | Spark Streaming (DStreams) | Monitoreo del directorio de entrada, Procesamiento en micro-lotes. |
| **Datos** | JSON Lines, Pandas | Manejo y transformación de estructuras de datos para el streaming. |

### **2.2. Diagrama de Flujo de Datos**

El sistema opera a través de un mecanismo de **micro-batching basado en archivos (JSON Lines)**.

\+------------------+     \+------------------+     \+--------------------------+  
|  FORMULARIO WEB  | \--\> | DJANGO / JSON Gen| \--\> | INPUT\_STREAMING Folder   |  
\+------------------+     \+------------------+     \+----------+---------------+  
          ^                      ^                         |  
          | (Polling AJAX)       | (Carga CSV)             | (DStreams)  
          |                      |                         v  
\+------------------+     \+------------------+     \+--------------------------+  
| DASHBOARD / UI   | \<-- | OUTPUT\_STREAMING | \<-- | SPARK STREAMING ENGINE   |  
| (Tiempo Real)    |     | (Resultados JSON)|     | (Carga Modelo MLlib)     |  
\+------------------+     \+------------------+     \+--------------------------+

### **2.3. Detalle del Flujo de Procesamiento**

#### **A. Flujo para Predicción Individual (Latencia Baja)**

1. El Agente llena el formulario web con los datos del cliente.  
2. **Django** serializa los datos a un archivo **JSON Lines** (un registro).  
3. El archivo se deposita en la carpeta de escucha (media/input\_streaming/).  
4. **Spark Streaming** lo detecta en el siguiente micro-lote.  
5. El modelo MLlib aplica la transformación y predicción.  
6. El resultado se escribe como JSON en la carpeta de salida (media/output\_streaming/).  
7. **JavaScript** (usando *polling*) detecta el archivo de resultado y lo muestra inmediatamente al usuario.

#### **B. Flujo para Procesamiento por Lotes (Alto Rendimiento)**

1. El Agente carga un archivo **CSV** (con N registros).  
2. **Django**/Pandas transforma el CSV en un archivo de **JSON Lines** (una línea por registro).  
3. El archivo se deposita en media/input\_streaming/.  
4. **Spark Streaming** procesa el lote completo en un micro-batch.  
5. Se generan N predicciones.  
6. Los resultados completos se guardan en la carpeta de salida.  
7. El **Dashboard** actualiza las métricas y la barra de progreso en tiempo real.

### **2.4. Tecnologías y Dependencias Requeridas**

Para la correcta ejecución del proyecto, se requiere la siguiente configuración de software y librerías, priorizando la compatibilidad entre el ecosistema Python/PySpark.

| Componente | Tecnología | Versión Requerida | Uso Específico |
| :---- | :---- | :---- | :---- |
| **Python** | Python | **3.10** (Recomendado) o 3.9 | Lenguaje principal para Django, PySpark y *scripts* de control. |
| **Backend** | Django | Última versión estable (Ej. 4.x o 5.x) | Desarrollo de la API web, gestión de archivos y la interfaz de usuario. |
| **API/Polling** | **Django REST Framework (DRF)** | Última versión estable | Desarrollo de los endpoints limpios y estructurados para el *polling* de JavaScript (estado, resultados). |
| **Web Server** | Gunicorn/WSGI | N/A | Servidor para Django (requerido para despliegue). |
| **Ecosistema Spark** | Java Development Kit (JDK) | 8 o 11 | **CRÍTICO:** Spark requiere Java para su ejecución. |
| **Motor de ML/Streaming** | Apache Spark | 3.x | La distribución binaria de Spark para el procesamiento distribuido. |
| **Librería PySpark** | pyspark | Compatible con Spark 3.x | Interface Python para utilizar Spark Core, Streaming y MLlib. |
| **Manejo de Datos** | pandas, **numpy** | Última versión estable | Utilizado por Django para leer y procesar archivos CSV antes de la serialización a JSON Lines. **NumPy es una dependencia fundamental de Pandas.** |
| **Visualización** | **Chart.js** | Última versión | Librería JavaScript para generar los gráficos de Dona/Barras en el Dashboard. |

## **3\. COMPONENTE DE MACHINE LEARNING (PYSPARK MLlib)**

### **3.1. Entrenamiento del Modelo (Fase Inicial)**

* **Dataset Base:** bank.csv (Datos de marketing bancario).  
* **Variable Objetivo ():** deposit (yes/no).  
* **Algoritmo:** **Random Forest Classifier** de MLlib.

### **3.2. Preprocesamiento y Pipeline ML**

El preprocesamiento es crucial para convertir las variables crudas en *features* numéricas que el modelo pueda interpretar.

\# Transformaciones en el Pipeline de MLlib:  
\# 1\. StringIndexer: Codificación de variables categóricas (job, marital, month, etc.)  
\# 2\. VectorAssembler: Combinación de todas las features en un vector único.  
\# 3\. StandardScaler: Opcional, para normalizar características numéricas.

pipeline \= Pipeline(stages=\[  
    \# ... StringIndexers para todas las variables categóricas  
    \# ... VectorAssembler para todas las features  
    RandomForestClassifier(featuresCol="features", labelCol="label", numTrees=100, maxDepth=10)  
\])

\# Persistencia: El pipeline entrenado debe guardarse para su uso en streaming.  
pipeline.fit(trainingData).write().overwrite().save("path/to/modelo\_clasificador")

### **3.3. Configuración de Spark Streaming**

El sistema utiliza DStreams de Spark Streaming para monitorear el sistema de archivos local.

| Configuración | Valor/Ruta | Descripción |
| :---- | :---- | :---- |
| **StreamingContext** | batchDuration \= 10 segundos | Intervalo de tiempo para el micro-batch. |
| **Carpeta de Escucha** | media/input\_streaming/ | Monitoreada por ssc.textFileStream(). |
| **Carpeta de Salida** | media/output\_streaming/ | Almacena los resultados procesados. |

### **3.4. Mecanismo de Inferencia en Streaming**

Para cada micro-batch (cada lote de archivos):

1. **Carga del Modelo:** El modelo entrenado se carga **una sola vez** al inicio del StreamingContext.  
2. **Lectura:** Los archivos JSON Lines son leídos como RDDs.  
3. **Conversión:** Cada RDD se convierte en un DataFrame de Spark.  
4. **Predicción:** El modelo MLlib aplica el transform() al DataFrame de entrada.  
5. **Escritura:** Los resultados (predicción, probabilidad) se serializan y se guardan en media/output\_streaming/.

## **4\. INTERFAZ DE USUARIO Y RESULTADOS**

### **4.1. Formato de Entrada de Datos**

Todos los datos de entrada (individuales o por lote) se normalizan al formato **JSON Lines** antes de entrar al *input\_streaming* para garantizar la uniformidad en el procesamiento de Spark.

**Ejemplo JSON Lines (Lote):**

{"age": 30, "job": "admin", "balance": 1800, "duration": 450, ...}  
{"age": 45, "job": "technician", "balance": 90, "duration": 120, ...}  
...

### **4.2. Formato de Salida de Resultados**

| Caso | Propósito | Estructura de Salida |
| :---- | :---- | :---- |
| **Individual** | Respuesta rápida y detallada para el Agente. | {"prediction": "yes", "probability": 0.85, "confidence": "high"} |
| **Lote** | Descarga y visualización de resultados agregados. | Lista de JSON con features clave \+ prediction y probability. |

### **4.3. Visualización en el Dashboard**

El Dashboard está diseñado para ofrecer una **visión en tiempo real** del rendimiento y el procesamiento.

* **KPIs en Tiempo Real:** Contador de lotes procesados y registros totales.  
* **Distribución:** Gráfico de Dona/Barras mostrando la distribución de las predicciones (Clientes **"Sí"** vs **"No"**).  
* **Estado del Sistema:** Indicador de actividad del **Spark Streaming** (Activo/Inactivo).  
* **Resultados Recientes:** Tabla con las últimas  predicciones procesadas.

## **5\. LÓGICA DE PROGRAMACIÓN Y FUNCIONALIDADES CLAVE (SIN CÓDIGO)**

Este apartado detalla las funciones lógicas o bloques de programación esenciales que deben ser implementados en cada componente para garantizar el flujo correcto de los datos, desde el formulario hasta el resultado final.

### **5.1. Lógica del Backend Django (Ingesta y Comunicación)**

Esta capa se encarga de recibir los datos del Agente, estandarizarlos y coordinar la comunicación con el motor Spark.

| Función Lógica | Responsabilidad Principal | Flujo Asociado |
| :---- | :---- | :---- |
| **handle\_prediccion\_individual()** | Gestiona la solicitud del formulario. Valida los campos de entrada, asigna un **ID de Trabajo único**, y llama a la función de serialización. | 2.3.A |
| **handle\_carga\_masiva\_csv()** | Gestiona el archivo CSV subido. Valida el formato y las columnas. Asigna un **ID de Trabajo único**, lee el CSV con Pandas, y llama a la función de serialización. | 2.3.B |
| **serializar\_a\_json\_lines(data, job\_id)** | **CRÍTICA:** Toma los datos estandarizados y los escribe en un archivo con el job\_id. Coloca el archivo en la carpeta de escucha: **media/input\_streaming/**. | 2.3.A, 2.3.B |
| **obtener\_estado\_trabajos()** | Lee los archivos en las carpetas input y output para construir el **Historial de Procesos** (Pendientes/Completados). | 6.3 |
| **obtener\_metricas\_dashboard()** | Lee los resultados agregados y calcula los KPIs: total de registros, distribución "Sí" vs "No", y el estado general de Spark. | 4.3 |
| **obtener\_resultado\_por\_id(job\_id)** | Busca y lee el archivo de resultado específico en media/output\_streaming/ para una predicción individual. | 2.3.A |

### **5.2. Lógica de PySpark ML (Entrenamiento Offline)**

Estas funciones se ejecutan para la creación del modelo inicial o durante un proceso de Reentrenamiento Periódico (Offline).

| Función Lógica | Responsabilidad Principal | Fase Asociada |
| :---- | :---- | :---- |
| **cargar\_y\_limpiar\_datos(path)** | Carga el dataset base y realiza la limpieza y preparación inicial de datos (Spark DataFrames). | 3.1 |
| **construir\_pipeline\_ml()** | Define la secuencia completa de transformación (StringIndexers, VectorAssembler) y el algoritmo (Random Forest). | 3.2 |
| **entrenar\_y\_evaluar\_modelo(pipeline)** | Ejecuta el entrenamiento y evalúa el modelo para verificar el criterio de . | 6.1 |
| **guardar\_modelo\_entrenado(model, path)** | Serializa y guarda todo el *pipeline* entrenado en la ubicación de disco que será utilizada por el proceso de *streaming*. | 3.2 |

### **5.3. Lógica de Spark Streaming (Motor de Inferencia Continua)**

Esta lógica corre en segundo plano de manera continua (24/7), esperando los archivos depositados por Django.

| Función Lógica | Responsabilidad Principal | Flujo Asociado |
| :---- | :---- | :---- |
| **iniciar\_contexto\_streaming(duration)** | Crea el StreamingContext y establece el intervalo de micro-lote (batchDuration \= 10 segundos). **CRÍTICA:** Debe llamar a cargar\_modelo\_persitido() inmediatamente después. | 3.3 |
| **cargar\_modelo\_persitido(path)** | Carga el *pipeline* entrenado del disco una sola vez y lo mantiene en memoria para la inferencia rápida. | 3.4 (Punto 1\) |
| **definir\_dstream\_input(input\_dir)** | Configura el monitor de archivos (ssc.textFileStream()) para la carpeta media/input\_streaming/. | 3.3 |
| **procesar\_micro\_batch(rdd)** | Lógica central: Itera sobre el lote de archivos JSON, convierte a DataFrame, aplica el transform() del modelo y extrae la predicción. | 3.4 |
| **escribir\_resultados\_output(dataframe\_predicho)** | Escribe el DataFrame predicho (con prediction y probability) como archivos **JSON Lines** en la carpeta de salida: **media/output\_streaming/**. | 3.4 (Punto 5\) |

### **5.4. Lógica del Frontend (JavaScript / HTML)**

Código ejecutado en el navegador del Agente para las interacciones en tiempo real.

| Función Lógica | Responsabilidad Principal | Flujo Asociado |
| :---- | :---- | :---- |
| **iniciar\_polling()** | Configura un temporizador para llamar periódicamente a las APIs de actualización del dashboard (Ej: cada 3 segundos). | 2.2 |
| **renderizar\_historial(data)** | Recibe la lista de trabajos (Pendientes/Completados) y actualiza la tabla del historial. | 6.3 |
| **mostrar\_resultado\_individual(data)** | Muestra el resultado de la predicción de Latencia Baja en un elemento visible (modal o panel). | 2.3.A |
| **actualizar\_visuales\_dashboard(data)** | Recibe las métricas agregadas y actualiza los gráficos (Dona/Barras) y contadores del Dashboard. | 4.3 |

## **6\. PLAN DE IMPLEMENTACIÓN DETALLADO**

### **6.1. Criterios de Aceptación Clave**

| Tipo | Criterio | Métrica Objetivo |
| :---- | :---- | :---- |
| **Funcional ML** | Precisión del Modelo |  |
| **Funcional Web** | Predicción Individual | Latencia  segundos |
| **Técnico Streaming** | Procesamiento por Lotes | Lote de 1000 registros en  segundos |
| **Técnico General** | Uso de Tecnologías | Arquitectura implementada sin librerías de terceros no especificadas (e.g., **No React/Vue**). |

### **6.2. Etapas del Desarrollo (Días 1-12)**

El proyecto se divide en 4 Fases principales con una duración estimada de **12 días de desarrollo activo**: ML Core (Días 1-3), Streaming (Días 4-6), Interfaz Web (Días 7-10), Integración y Testing (Días 11-12).

### **6.3. Gestión de Procesos Concurrentes (Historial)**

Para soportar la concurrencia de tareas (subir múltiples CSV o formularios a la vez), la interfaz de usuario deberá implementar un **Gestor de Procesos (Historial)** basado en el sistema de archivos:

1. **Monitoreo del *Input***: Django listará los archivos presentes en media/input\_streaming/. Estos archivos representan **Trabajos Pendientes** de ser recogidos por el motor Spark.  
2. **Monitoreo del *Output***: Django listará los archivos de resultado en media/output\_streaming/. Estos representan **Trabajos Finalizados**.  
3. **Visualización en Dashboard**: Se debe proporcionar una sección que muestre el estado de los trabajos subidos (CSV y formularios individuales) para que el Agente pueda hacer seguimiento al progreso y descargar los resultados una vez listos.

## **7\. GESTIÓN DE RIESGOS Y ERRORES**

### **7.1. Estrategia de Logging**

Se debe implementar **logging detallado** en los tres componentes principales (Django, MLlib, Spark Streaming) para facilitar la depuración. Los mensajes deben incluir la marca de tiempo, el nivel de error y el archivo/función de origen.

### **7.2. Manejo de Errores Comunes**

| Error Potencial | Causa Principal | Solución Recomendada |
| :---- | :---- | :---- |
| **Fallo de Spark** | Variables de entorno (JAVA\_HOME, SPARK\_HOME) incorrectas. | Verificar la instalación de **Java 8** y la configuración de rutas de entorno. |
| **Fallo de Predicción** | Formato de archivo JSON incorrecto (no es JSON Lines). | Implementar validación estricta de formato en **Django/Pandas** antes de depositar el archivo. |
| **Polling Ineficiente** | JavaScript no encuentra la ruta de los resultados. | Validar la ruta de lectura de media/output\_streaming/ y el formato de respuesta del JSON. |
| **Modelo Incompatible** | El modelo fue guardado con una versión diferente de MLlib/Spark. | Asegurar que la versión usada para entrenar el modelo sea idéntica a la usada en el StreamingContext. |

## **8\. EXTENSIONES FUTURAS**

### **8.1. Mejoras Inmediatas**

* Más algoritmos de ML para comparar.  
* Dashboard más elaborado.  
* Sistema de autenticación.  
* Exportación de reportes.

### **8.2. Para Producción y Escalabilidad (Dataset Acumulado)**

* **Dataset Histórico Acumulado:** Implementar un proceso para consolidar todos los datos procesados (bank.csv \+ formularios \+ nuevos CSV) en un único repositorio (idealmente en formato **Parquet**), creando la base para el reentrenamiento del modelo.  
* **Persistencia de Historial (BD)**: Utilizar una base de datos relacional (PostgreSQL) para guardar los resultados de las predicciones a largo plazo y facilitar consultas históricas.  
* **Reentrenamiento Periódico (Offline Retraining):** Ejecutar el proceso de entrenamiento del modelo (Fase 1\) de forma periódica (ej. semanal o mensual) utilizando el **Dataset Histórico Acumulado** completo. Una vez entrenado, el nuevo modelo se carga en el motor de Spark Streaming, reemplazando la versión anterior sin interrumpir el servicio.  
* Spark cluster distribuido (usando **Hadoop/YARN**).  
* Sistema de colas (Kafka).  
* Monitorización avanzada.