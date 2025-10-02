<#
PowerShell helper para instalar/configurar un JDK (manual) y winutils
Instrucciones:
1. Descarga e instala un JDK 11 o 17 (por ejemplo Liberica/OpenJDK).
2. Ejecuta este script con privilegios de administrador para establecer las variables de entorno (temporal para la sesión):

   .\setup_java_windows.ps1 -JavaPath 'C:\Program Files\BellSoft\LibericaJDK-17'

3. Para winutils: descarga una build de winutils.exe compatible y coloca en C:\hadoop\bin y ejecuta:
   .\setup_java_windows.ps1 -SetHadoop

#>
param(
    [string]$JavaPath = '',
    [switch]$SetHadoop
)

if ($JavaPath -ne '') {
    if (-Not (Test-Path $JavaPath)) {
        Write-Error "La ruta $JavaPath no existe"
        exit 1
    }
    Write-Host "Estableciendo JAVA_HOME=$JavaPath (solo para la sesión actual)"
    $env:JAVA_HOME = $JavaPath
    $env:PATH = "$JavaPath\bin;" + $env:PATH
    Write-Host "JAVA_HOME set. Verifica con: java -version"
}

if ($SetHadoop) {
    $hadoop = 'C:\hadoop'
    if (-Not (Test-Path $hadoop)) {
        New-Item -ItemType Directory -Path $hadoop | Out-Null
    }
    Write-Host "Por favor coloca winutils.exe en $hadoop\bin y luego establece HADOOP_HOME permanentemente."
    $env:HADOOP_HOME = $hadoop
    Write-Host "HADOOP_HOME seteado temporalmente a $hadoop"
}

Write-Host "Nota: este script no instala JDK ni winutils por ti. Solo ayuda a apuntar las variables en la sesión actual. Para cambios permanentes, usa System Properties > Environment Variables."
