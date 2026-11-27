# Barbería Clase A — Django + PostgreSQL

## Contenido

- `Dockerfile` → define la imagen del contenedor de Django.
- `docker-compose.yml` → levanta Django y PostgreSQL 17 en contenedores separados.
- `requirements.txt` → dependencias de Python.
- `entrypoint.sh` → espera a la base de datos, aplica migraciones y arranca el servidor.
- `.env.example` → variables de entorno de ejemplo (copiar como `.env`).
- `manage.py`, `config/` → configuración del proyecto Django.
- `core/`, `api/` y las apps de negocio → vistas, endpoints y modelos del sistema.
- `scripts/` → migración reproducible desde Supabase y SQL auxiliares.

## Primeros pasos

1. En PowerShell, copien `.env.example` como `.env` y cambien las credenciales
   locales si lo necesitan:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Levanten los contenedores:
   ```
   docker compose up --build
   ```
   PostgreSQL usa la imagen oficial `postgres:17.12-alpine`; Django espera a
   que el servicio de base esté saludable y aplica las migraciones al iniciar.

3. Abran en el navegador:
   ```
   http://localhost:8000
   ```
   Django se conecta al servicio PostgreSQL local. El esquema lo crean las
   migraciones de Django. En esta instalación la base ya tiene los datos
   migrados desde el proyecto original de Supabase (ver "Migración desde
   Supabase"). Si clonan el repo en otra máquina, la base se crea vacía y
   pueden cargar los datos con el script de migración.

4. Prueben también el endpoint de ejemplo de la API REST:
   ```
   http://localhost:8000/api/estado/
   ```
   Debería devolver un JSON simple confirmando que la API funciona.

5. Para entrar a una terminal dentro del contenedor (correr comandos de manage.py, instalar algo, etc.):
   ```
   docker compose exec web bash
   ```

6. Para crear una app nueva de Django (por ejemplo, la app principal de su sistema):
   ```
   docker compose exec web python manage.py startapp nombre_app
   ```
   No se olviden de agregarla a `INSTALLED_APPS` en `config/settings.py`.

7. Para crear y aplicar migraciones después de modificar un modelo:
   ```
   docker compose exec web python manage.py makemigrations
   docker compose exec web python manage.py migrate
   ```

8. Para apagar todo:
   ```
   docker compose down
   ```
   (Los datos de la base de datos NO se pierden: quedan en el volumen
   `postgres_data`. Si quieren borrar todo desde cero, usen `docker compose down -v`).

## Migración desde Supabase

Este proyecto se migró desde un proyecto de Supabase que corría PostgreSQL
17.11. La base local usa PostgreSQL 17.12 (`postgres:17.12-alpine`), la misma
versión mayor; el cliente `pg_dump` 17.12 puede volcar sin problemas un
servidor 17.11.

La estrategia es: **Django crea el esquema con sus migraciones y de Supabase
solo se copian los datos**. No se restaura el esquema completo de Supabase
porque las migraciones locales están regeneradas y no coinciden con las 45
migraciones históricas del proyecto remoto; además, el dump completo arrastra
RLS, roles de Supabase y la tabla legacy `empleado_cuentas`.

Qué se migra:

- Todas las tablas de negocio y las tablas de Django (`auth_*`, `authtoken`,
  `django_*`) del schema `public`.
- Se preservan los 3 grupos (`Cajero`, `Barbero`, `Administrador`), sus 212
  permisos, los 5 usuarios, los tokens y el historial del admin.

Qué NO se migra:

- `django_migrations` (la base local usa las migraciones del repo).
- `empleado_cuentas` (tabla legacy, vacía, ya no existe en los modelos).
- Los schemas administrados por Supabase (`auth`, `storage`, `realtime`,
  `vault`): están vacíos y la app no los usa.

### Re-exportar e importar

El script `scripts/migrar-supabase.ps1` hace todo el proceso:

```powershell
# 1. Completar scripts/supabase.env (copiar de supabase.env.example)

# Opcion A: hacer todo (exportar + importar)
.\scripts\migrar-supabase.ps1

# Opcion B: por separado
.\scripts\migrar-supabase.ps1 -SoloExportar   # solo backup, no toca la base
.\scripts\migrar-supabase.ps1 -SoloImportar   # importa lo ya exportado
```

Si PowerShell bloquea el script por la política de ejecución, corranlo así:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\migrar-supabase.ps1
```

Usen el puerto **5432** del pooler de Supabase (session mode). El 6543 es el
transaction pooler y no sirve para `pg_dump`.

### Seguridad

- `backups/` contiene datos personales (clientes, teléfonos) y hashes de
  contraseñas. Está en `.gitignore`; no lo suban al repo.
- `scripts/supabase.env` contiene las credenciales de Supabase. También está
  en `.gitignore`. Después de migrar conviene rotar la contraseña en Supabase
  y borrar ese archivo.
- El archivo `.env` local también está en `.gitignore`.

## API REST (Django REST Framework)

El proyecto ya trae `djangorestframework` instalado y configurado
(`rest_framework` está en `INSTALLED_APPS`, con paginación básica en
`REST_FRAMEWORK` dentro de `config/settings.py`). La app `api/` incluye un
endpoint de ejemplo (`EstadoAPIView`) que pueden usar como modelo para los
suyos.

Para agregar un endpoint real sobre un modelo de su organización:

1. Definan el modelo en la app correspondiente (por ejemplo, `Clientes` en la
   app `turnos`).
2. Creen un archivo `serializers.py` en esa app, con una clase
   `ClienteSerializer(serializers.ModelSerializer)`.
3. Creen una vista (por ejemplo, `ClienteListView(generics.ListCreateAPIView)`)
   que use ese serializer.
4. Registren la ruta en `config/urls.py`, agrupada bajo `/api/`, por ejemplo:
   `path('api/turnos/', include('turnos.urls'))`.

### Productos

- `/api/productos/` y `/api/productos/<id_producto>/`: listado, alta, detalle,
  edición parcial y eliminación de productos.
- `/api/marcas/`, `/api/categorias/` y `/api/descuentos/`: listados para los
  selectores del catálogo.
- `/api/productos/precios/`: último costo unitario de compra y último precio
  unitario de venta por producto, obtenidos de sus detalles de transacción.
  Son datos históricos y no se editan desde el CRUD de productos.
- No se agregan columnas ni migraciones: los precios provienen de compras y
  ventas; el modelo de productos conserva sus campos y relaciones actuales.

### Compras

- `GET /api/compras/`: historial paginado de compras con sus productos,
  cantidades y costos unitarios.
- `POST /api/compras/`: registra una compra y aumenta el stock dentro de una
  transacción. El importe por línea y el total se calculan en el servidor.

  ```json
  {
    "detalles": [
      { "id_producto": 1, "cantidad": 4, "precio_unitario": "1250.00" }
    ]
  }
  ```

### Acceso a la API

Por el momento, las rutas de administración de empleados, grupos y
productos no requieren login. Esto es solo para desarrollo: cualquier cliente
que alcance la API puede crear, modificar o eliminar estos registros, por lo
que no se debe exponer el backend a Internet con esta configuración. El
endpoint público de barberos sigue mostrando únicamente los datos necesarios
para reservar.

Las cuentas de empleados se vinculan directamente con usuarios de Django
(`auth_user`). El grupo `Barbero` identifica a quienes aparecen en el endpoint
público de barberos y en el resumen del dashboard.

Los grupos disponibles para asignar a empleados deben existir previamente en
Django; el CRUD no crea ni modifica grupos. Al eliminar desde el CRUD un
empleado asociado a una cuenta, esa cuenta queda desactivada en lugar de
eliminarse. Apliquen las migraciones después de levantar la base de datos:

```
docker compose exec web python manage.py migrate
```

## Adaptar a su proyecto

- Cambien `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` en `.env` por
  el nombre de su organización.
- Reemplacen la vista de `core/views.py` y su template por las páginas reales
  de su sistema, o creen apps nuevas para cada módulo (ver paso 7).
- El código del proyecto vive montado en tiempo real: no hace falta
  reconstruir la imagen cada vez que cambian un archivo `.py`, solo si
  cambian `requirements.txt`.
- Si agregan una librería nueva, súmenla a `requirements.txt` y reconstruyan
  con `docker compose up --build`.

## Estructura del proyecto

```
.
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── entrypoint.sh
├── .env.example
├── manage.py
├── config/          # configuración global del proyecto (settings, urls)
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── core/            # app de ejemplo (vista de inicio, reemplazar/ampliar)
│   ├── views.py
│   ├── models.py
│   └── templates/core/home.html
├── api/             # app de ejemplo para la API REST
│   ├── views.py
│   └── urls.py
└── scripts/         # migración desde Supabase y SQL auxiliares
    ├── migrar-supabase.ps1
    ├── supabase.env.example
    └── sql/
        ├── truncate_public.sql
        ├── reset_sequences.sql
        └── verify_counts.sql
```

## Cambios de esquema

Las tablas de negocio están gestionadas por Django (`managed = True`). Las
migraciones del repo son la fuente de verdad del esquema: no hace falta
`inspectdb` ni volver a marcar `managed = False`. Para añadir o modificar una
tabla, actualicen el modelo correspondiente y generen/apliquen la migración:

```
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

Los puertos locales predeterminados son `8000` para Django y `5432` para
PostgreSQL. Si uno ya está ocupado, cambien `DJANGO_HOST_PORT` o
`POSTGRES_HOST_PORT` en `.env`. Los datos sobreviven a `docker compose down`
gracias al volumen `postgres_data`. `docker compose down -v` elimina ese volumen
y borra permanentemente los datos locales.

Esta configuración incluye PostgreSQL y el backend Django; no incluye otros
servicios de base de datos o plataforma.

---

ISDEM | Barbería Clase A
