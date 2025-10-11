$hadoopDir = "D:\Evidencia03v02\data\hadoop"
$binDir = Join-Path $hadoopDir "bin"
$winutilsUrl = "https://github.com/cdarlint/winutils/raw/master/hadoop-3.2.2/bin/winutils.exe"
$hadoopDllUrl = "https://github.com/cdarlint/winutils/raw/master/hadoop-3.2.2/bin/hadoop.dll"

# Crear directorios si no existen
New-Item -ItemType Directory -Force -Path $binDir | Out-Null

# Descargar winutils.exe
Invoke-WebRequest -Uri $winutilsUrl -OutFile (Join-Path $binDir "winutils.exe")

# Descargar hadoop.dll
Invoke-WebRequest -Uri $hadoopDllUrl -OutFile (Join-Path $binDir "hadoop.dll")

# Establecer variable de entorno HADOOP_HOME
[System.Environment]::SetEnvironmentVariable("HADOOP_HOME", $hadoopDir, [System.EnvironmentVariableTarget]::User)

Write-Host "Hadoop binaries instalados en $hadoopDir"
Write-Host "Variable de entorno HADOOP_HOME establecida"