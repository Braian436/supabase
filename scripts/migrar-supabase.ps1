#Requires -Version 5.1
<#
.SYNOPSIS
    Migra los datos del schema public de Supabase a la base local de Docker.

.DESCRIPTION
    Hace tres cosas:
      1. Guarda un backup completo de public (formato custom + SQL plano).
      2. Exporta solo los datos, sin django_migrations ni empleado_cuentas.
      3. Importa esos datos en el PostgreSQL local dentro de una transaccion,
         ajusta las secuencias y verifica los conteos.

    El esquema local NO se restaura desde Supabase: lo crea Django con sus
    migraciones. Solo se copian los datos.

.PARAMETER EnvFile
    Archivo con las credenciales de Supabase. Por defecto scripts/supabase.env.

.PARAMETER SoloExportar
    Solo genera los backups en backups/ y no toca la base local.

.PARAMETER SoloImportar
    Usa los archivos ya existentes en backups/ y no vuelve a consultar Supabase.

.PARAMETER Force
    No pide confirmacion antes de borrar los datos locales.

.EXAMPLE
    .\scripts\migrar-supabase.ps1

.EXAMPLE
    .\scripts\migrar-supabase.ps1 -SoloExportar

.NOTES
    Requiere Docker Desktop y el stack de docker-compose.yml.
    El archivo scripts/supabase.env contiene credenciales y esta en .gitignore.
#>
[CmdletBinding()]
param(
    [string]$EnvFile,
    [string]$ProjectRoot,
    [switch]$SoloExportar,
    [switch]$SoloImportar,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

# $PSScriptRoot no siempre esta disponible en los valores por defecto de param
# en Windows PowerShell 5.1, asi que resolvemos las rutas aca.
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $scriptDir }
if (-not $EnvFile) { $EnvFile = Join-Path $scriptDir 'supabase.env' }

function Leer-Env([string]$ruta) {
    if (-not (Test-Path $ruta)) {
        throw "No existe $ruta. Copia scripts/supabase.env.example y completa los datos."
    }

    $mapa = @{}
    Get-Content $ruta | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
            $mapa[$matches[1]] = $matches[2].Trim('"').Trim("'")
        }
    }
    return $mapa
}

$root = (Resolve-Path $ProjectRoot).Path
$backups = Join-Path $root 'backups'
$pgImage = 'postgres:17.12-alpine'
New-Item -ItemType Directory -Force -Path $backups | Out-Null

if (-not $SoloImportar) {
    $cfg = Leer-Env $EnvFile
    $hostSupabase = $cfg['SUPABASE_HOST']
    $puerto = if ($cfg['SUPABASE_PORT']) { $cfg['SUPABASE_PORT'] } else { '5432' }
    $base = if ($cfg['SUPABASE_DB']) { $cfg['SUPABASE_DB'] } else { 'postgres' }
    $usuario = $cfg['SUPABASE_USER']
    $clave = $cfg['SUPABASE_PASSWORD']

    if (-not $hostSupabase -or -not $usuario -or -not $clave) {
        throw 'Faltan SUPABASE_HOST, SUPABASE_USER o SUPABASE_PASSWORD en el archivo de entorno.'
    }
    if ($puerto -eq '6543') {
        Write-Warning 'El puerto 6543 es el transaction pooler; para pg_dump se usa 5432.'
        $puerto = '5432'
    }

    $conexion = "host=$hostSupabase port=$puerto user=$usuario dbname=$base sslmode=require"

    Write-Host '>> Backup completo de public (formato custom)...'
    docker run --rm -v "${backups}:/backups" -e "PGPASSWORD=$clave" $pgImage pg_dump $conexion --format=custom --schema=public --no-owner --no-privileges -f /backups/supabase_public.dump
    if ($LASTEXITCODE -ne 0) { throw 'Fallo el backup completo en formato custom.' }

    Write-Host '>> Backup completo de public (SQL plano)...'
    docker run --rm -v "${backups}:/backups" -e "PGPASSWORD=$clave" $pgImage pg_dump $conexion --schema=public --no-owner --no-privileges -f /backups/supabase_public.sql
    if ($LASTEXITCODE -ne 0) { throw 'Fallo el backup completo en SQL plano.' }

    Write-Host '>> Exportando solo datos (sin django_migrations ni empleado_cuentas)...'
    docker run --rm -v "${backups}:/backups" -e "PGPASSWORD=$clave" $pgImage pg_dump $conexion --data-only --schema=public --exclude-table=public.django_migrations --exclude-table=public.empleado_cuentas --no-owner --no-privileges -f /backups/supabase_data.sql
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la exportacion de datos.' }

    Write-Host '>> Limpiando meta-comandos y setval del dump de datos...'
    $sed = "sed -e '/^\\restrict /d' -e '/^\\unrestrict /d' -e '/^SELECT pg_catalog[.]setval/d' /backups/supabase_data.sql > /backups/supabase_data_clean.sql"
    docker run --rm -v "${backups}:/backups" $pgImage sh -c $sed
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la limpieza del dump de datos.' }

    Write-Host '>> Exportacion lista en backups/.'
}

if ($SoloExportar) { return }

$local = Leer-Env (Join-Path $root '.env')
$dbUser = $local['POSTGRES_USER']
$dbName = $local['POSTGRES_DB']
if (-not $dbUser -or -not $dbName) {
    throw 'Faltan POSTGRES_USER o POSTGRES_DB en .env.'
}

if (-not $Force) {
    Write-Warning 'La importacion BORRA los datos actuales de public (menos django_migrations) y los reemplaza por los de Supabase.'
    $respuesta = Read-Host 'Escribi SI para continuar'
    if ($respuesta -ne 'SI') {
        Write-Host 'Cancelado.'
        return
    }
}

Push-Location $root
try {
    Write-Host '>> Levantando PostgreSQL y aplicando migraciones...'
    docker compose up -d --build
    if ($LASTEXITCODE -ne 0) { throw 'Fallo docker compose up.' }

    docker compose exec -T web python manage.py migrate
    if ($LASTEXITCODE -ne 0) { throw 'Fallo manage.py migrate.' }

    Write-Host '>> Copiando archivos al contenedor db...'
    docker compose cp (Join-Path $backups 'supabase_data_clean.sql') db:/tmp/supabase_data_clean.sql
    docker compose cp (Join-Path $root 'scripts\sql\truncate_public.sql') db:/tmp/truncate_public.sql
    docker compose cp (Join-Path $root 'scripts\sql\reset_sequences.sql') db:/tmp/reset_sequences.sql
    docker compose cp (Join-Path $root 'scripts\sql\verify_counts.sql') db:/tmp/verify_counts.sql

    Write-Host '>> Importando datos en una sola transaccion...'
    docker compose exec -T db psql -U $dbUser -d $dbName -v ON_ERROR_STOP=1 -1 -f /tmp/truncate_public.sql -f /tmp/supabase_data_clean.sql
    if ($LASTEXITCODE -ne 0) { throw 'Fallo la importacion (la transaccion se revirtio).' }

    Write-Host '>> Ajustando secuencias...'
    docker compose exec -T db psql -U $dbUser -d $dbName -v ON_ERROR_STOP=1 -f /tmp/reset_sequences.sql
    if ($LASTEXITCODE -ne 0) { throw 'Fallo el ajuste de secuencias.' }

    Write-Host '>> Conteos finales:'
    docker compose exec -T db psql -U $dbUser -d $dbName -f /tmp/verify_counts.sql

    Write-Host '>> Verificando Django...'
    docker compose exec -T web python manage.py check
    if ($LASTEXITCODE -ne 0) { throw 'Fallo manage.py check.' }
}
finally {
    Pop-Location
}

Write-Host '>> Migracion terminada.'
