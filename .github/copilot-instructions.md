# Instrucciones para compañeros que usen agentes AI (Copilot / similares)

Este archivo contiene pautas prácticas y de seguridad para compañeros que usen un agente (Copilot, ChatGPT integrado, u otro) para modificar o ejecutar cosas en este repositorio.
Está pensado para evitar errores comunes (rutas incorrectas, comandos ejecutados desde el directorio equivocado, ejecución accidental de procesos pesados, etc.).

IMPORTANTE: las instrucciones están en español. Léelas antes de pedir al agente que ejecute comandos o haga cambios automáticos.

## Reglas de seguridad básicas
- Nunca pidas al agente que ejecute comandos que modifiquen el sistema fuera de la carpeta del proyecto (por ejemplo, borrar carpetas en C:\). Comprueba siempre la ruta de trabajo.
- Antes de ejecutar un comando que inicie procesos (Spark, servidores, scripts de larga duración), revisa el comando y verifica que se use el `python` del `venv` del proyecto.
- No incluyas credenciales o secretos en mensajes al agente. Si necesitas configurar variables de entorno, usa un archivo `.env` local (no subirlo al repo) y documenta su contenido en `.env.example`.

## Rutas y estructura relevante (esta copia puede cambiar si alguien reestructura el repo)
- Raíz del proyecto: `D:\Proyectos python\Evidencia03` (o la ruta donde hayas clonado el repo)
- Proyecto Django: `bankprocessor/` (contiene `manage.py`)
- App principal: `bankprocessor/processor/`
- Datasets: `data/` (coloca `bank.csv` aquí)
- Virtualenv (recomendado): `venv/` en la raíz del proyecto (opcional, puede estar en otro sitio)

## Comandos seguros y habituales (PowerShell)

Abrir PowerShell y activar el venv (desde la raíz del repo):

```powershell
cd "D:\Proyectos python\Evidencia03"
.\venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
pip install -r requirements.txt
```

Migraciones y servidor de desarrollo (usa el Python del venv):

```powershell
cd bankprocessor
..\venv\Scripts\python.exe manage.py migrate
..\venv\Scripts\python.exe manage.py runserver
```

Ejecutar un job (útil para debugging, ejecuta en `bankprocessor/`):

```powershell
..\venv\Scripts\python.exe manage.py run_job <job_id>
```

Si lanzas jobs desde la UI (la vista `process_data` hace un `subprocess.Popen`), revisa los logs `job_logs/run_job_<id>.log` en la carpeta donde está `manage.py`.

## Qué pedirle al agente y qué evitar
- Puedes pedir al agente que:
	- Edite plantillas, vistas y archivos de configuración siguiendo convenciones del repo.
	- Añada tests simples y cambios pequeños (p. ej., nuevas columnas en templates).
	- Cree scripts auxiliares en `tools/` para reproducir problemas localmente.
- Evita pedir al agente que:
	- Ejecute comandos de sistema sin comprobar la ruta y el venv (por ejemplo, `rm -rf` o `del /S`).
	- Modifique archivos `.env`, credenciales o conectores de producción.
	- Instale dependencias globales sin confirmación (prefiere `pip install -r requirements.txt`).

## Logs y depuración
- Los procesos lanzados desde la UI crean `job_logs/run_job_<id>.log` junto a `manage.py`. Revisa ese archivo si un job no avanza.
- Si el agente sugiere ejecutar un job en primer plano para depurar, ejecuta el comando `manage.py run_job <id>` desde `bankprocessor/` y observa la salida en la terminal.

## PySpark y Windows
- PySpark en Windows puede requerir `winutils.exe`. En este proyecto se colocó una copia para pruebas locales en `bankprocessor/hadoop/bin`. Si el agente sugiere mover archivos del sistema, confirma con el equipo.
- Para evitar errores de worker (Python worker crashed), usa el Python del `venv` y asegúrate de no iniciar más de un `SparkContext` en el mismo proceso.

## Actitudes recomendadas al usar un agente
- Antes de aceptar cambios grandes propuestos por el agente, revisa el diff y comprueba:
	- Que no se añadan credenciales o rutas absolutas.
	- Que no se cambie la base de datos de desarrollo sin migraciones documentadas.
- Pide al agente que genere pruebas mínimas cuando modifique lógica crítica (por ejemplo, creación de `BatchResult`).

## Qué hacer si algo sale mal
- Si el servidor no arranca, revisa `manage.py runserver` output en la terminal y los logs del proyecto.
- Si un job no crea `BatchResult`, busca `job_logs/run_job_<id>.log` y comparte las últimas 200 líneas con la persona que te asista.

## Actualizar estas instrucciones
- Si introduces nuevos flujos (p. ej., integración con Celery/Redis), actualiza este archivo con los pasos operativos y las advertencias de seguridad.

---

Este documento está pensado para evitar pasos peligrosos y acelerar la colaboración. Si quieres, puedo añadir un checklist para reviewers que usan agentes antes de aceptar PRs (p. ej., comprobar que no haya secrets, tests, README actualizado). ¿Lo agrego? 
 
## Checklist para reviewers que usan agentes
Antes de aceptar cambios propuestos por un agente (o por otra persona que haya usado un agente), sigue esta checklist rápida:

- [ ] Revisar el diff completo: buscar rutas absolutas, secretos, credenciales o cambios en archivos sensibles (`.env`, `settings.py`, CI).
- [ ] Confirmar que las dependencias nuevas están añadidas a `requirements.txt` y justificadas en el PR.
- [ ] Ejecutar tests locales (si existen) o al menos realizar un `python -m pyflakes .` / `flake8` rápido para detectar errores obvios.
- [ ] Verificar que los cambios en la base de datos vienen con migraciones y que las migraciones tienen sentido.
- [ ] Revisar cambios en scripts que ejecutan procesos (p. ej., `manage.py`, launchers) para asegurar que usan el `venv` y rutas relativas.
- [ ] Comprobar que no se añaden artefactos pesados (modelos, datasets) en el repo; preferir almacenamiento externo si es necesario.
- [ ] Probar manualmente el flujo crítico si es fácil (arrancar servidor dev y ejecutar un job simple) y revisar `job_logs/run_job_<id>.log` si procede.
- [ ] Confirmar que el README y/o `.github/copilot-instructions.md` se han actualizado si el cambio modifica el flujo de trabajo.

Si quieres, puedo convertir esta checklist en un template de PR o en un `pull_request_template.md` para que aparezca automáticamente en nuevos PRs.