#!/bin/bash
# ============================================================================
# Backup de la base ANTES de tocar nada. Corré esto conectado por SSH al
# droplet, antes de correr cualquier script de corrección.
#
# Ajustá estos 3 valores a los tuyos:
#   NOMBRE_BASE   -> el nombre de tu base de datos Postgres
#   USUARIO_DB    -> el usuario de Postgres que usás para conectarte
#   (te va a pedir la contraseña si no tenés PGPASSWORD configurado)
# ============================================================================

NOMBRE_BASE="tu_base"
USUARIO_DB="tu_usuario"
FECHA=$(date +%Y%m%d_%H%M%S)
ARCHIVO="backup_${NOMBRE_BASE}_${FECHA}.dump"

pg_dump -U "$USUARIO_DB" -h localhost -d "$NOMBRE_BASE" -F c -f "$ARCHIVO"

echo "Backup guardado en: $ARCHIVO"
echo "Para restaurar (si hiciera falta): pg_restore -U $USUARIO_DB -h localhost -d $NOMBRE_BASE -c $ARCHIVO"

# Tip: copiá ese archivo fuera del droplet (a tu compu, o a S3/algún storage
# aparte) para que si algo le pasa al servidor no dependas de un backup que
# vive en la misma máquina.
