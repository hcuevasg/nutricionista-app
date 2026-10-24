#!/usr/bin/env bash
# Carga en Railway las credenciales de Cloudflare R2 para los respaldos automáticos.
# Los valores se escriben sin mostrarse y van directo a Railway (no quedan en el historial).
# Uso: bash backend/scripts/configurar_respaldos_r2.sh   (requiere `railway login`)
set -euo pipefail

SERVICE="nutricionista-app"
echo "Respaldos automáticos a Cloudflare R2 → servicio $SERVICE en Railway"
echo

read -r  -p "Account ID de Cloudflare: " ACCOUNT_ID
read -r  -p "Nombre del bucket [nutriapp-backups]: " BUCKET
BUCKET="${BUCKET:-nutriapp-backups}"
read -r  -p "Access Key ID: " ACCESS_KEY_ID
read -rs -p "Secret Access Key (no se muestra): " SECRET_ACCESS_KEY
echo

for v in ACCOUNT_ID ACCESS_KEY_ID SECRET_ACCESS_KEY; do
  if [ -z "${!v}" ]; then echo "Falta $v; no se cambió nada."; exit 1; fi
done

railway variables --service "$SERVICE" \
  --set "R2_ACCOUNT_ID=$ACCOUNT_ID" \
  --set "R2_BUCKET=$BUCKET" \
  --set "R2_ACCESS_KEY_ID=$ACCESS_KEY_ID" \
  --set "R2_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY" > /dev/null

# Comprobar lo que quedó realmente en Railway (solo los últimos 4 caracteres)
SAVED=$(railway variables --service "$SERVICE" --kv | grep '^R2_ACCESS_KEY_ID=' | cut -d= -f2-)
echo
echo "Access Key ID ingresado termina en: ${ACCESS_KEY_ID: -4}"
echo "Access Key ID en Railway termina en: ${SAVED: -4}"
if [ "$SAVED" != "$ACCESS_KEY_ID" ]; then
  echo "ERROR: Railway no quedó con la clave ingresada. Revisa que estés en el proyecto correcto (railway status)."
  exit 1
fi
echo "Listo: variables R2 cargadas en $SERVICE. Railway redesplegará el backend y hará el primer respaldo al arrancar."
