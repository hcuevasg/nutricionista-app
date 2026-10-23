# Seguridad de NutriApp

## Variables de entorno (Railway, servicio nutricionista-app)

| Variable | Obligatoria | Para qué |
|---|---|---|
| `SECRET_KEY` | Sí | Firma de las sesiones (JWT). Sin ella el backend no arranca en producción. |
| `DATA_ENCRYPTION_KEY` | Sí | Cifra los datos de salud en la base. Generar con `python backup_r2.py genkey` y guardar copia fuera de Railway: **sin esta clave los datos cifrados no se pueden leer**. Para rotarla: `nueva,anterior`. |
| `REGISTRATION_CODE` | Para crear cuentas | Código de invitación del registro. Sin él, el registro está cerrado en producción. |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_WORKSPACE_ID` | Para la IA | Solo en el backend; nunca llegan al navegador. |
| `R2_*`, `BACKUP_ENCRYPTION_KEY` | Para backups | Ver `backend/backup_r2.py`. |
| `ACCESS_TOKEN_EXPIRE_HOURS` | No (12) | Duración de la sesión. |
| `ENABLE_API_DOCS` | No | `true` publica `/docs`; por defecto solo en desarrollo. |

El frontend (Vercel) solo recibe `VITE_API_URL`.

## Controles

- **Secretos**: ningún secreto versionado (revisado el historial completo); `.env*` ignorados.
- **Base de datos**: privada, solo la usa el backend con credenciales de Railway. El navegador nunca se conecta a ella.
- **Aislamiento entre cuentas**: cada consulta filtra por profesional; `tests/test_multitenant.py` recorre todas las rutas del API intentando leer o modificar datos de otra cuenta.
- **Autenticación**: todas las rutas exigen sesión salvo login, registro, segundo paso del 2FA, portal del paciente (token aleatorio, revocable y con vencimiento) y `/health`.
- **Sesiones**: token Bearer de 12 h (sin cookies, inmune a CSRF) con versión: cambiar la contraseña o el 2FA, o "cerrar sesión en todos los dispositivos", invalida los tokens anteriores. CSP estricta contra XSS.
- **Contraseñas**: bcrypt costo 12, mínimo 8 caracteres, bloqueo de 15 min tras 5 intentos fallidos, 2FA TOTP opcional con códigos de un solo uso.
- **Cifrado**: HTTPS (HSTS) en tránsito; Fernet en reposo para antecedentes, notas SOAP, alergias, notas, metas, dirección y secreto 2FA. Nombre, correo, teléfono y fecha de nacimiento quedan en claro para poder buscar.
- **Rate limiting y bots**: por IP en login/registro/2FA, acciones sensibles, IA, portal y reporte de errores, más un límite general; registro solo por invitación.
- **Entradas**: Pydantic valida tipos y largos (según la columna); requests de máximo 1 MB; logo solo PNG/JPEG/WebP ≤500 KB re-codificado; campos que controla el servidor no se aceptan desde el cliente; SQLAlchemy parametriza todas las consultas.
- **Contenido**: React escapa el HTML; los PDF escapan todo texto (ReportLab interpreta etiquetas).
- **Respuestas**: solo los campos necesarios (p. ej. el portal no expone cálculos internos ni notas), errores 500 sin detalles internos, `Cache-Control: no-store`.
