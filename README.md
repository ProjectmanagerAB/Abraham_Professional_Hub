# Abraham Professional Hub · v3

Portafolio profesional interactivo en Streamlit con dos modos separados:

- **Vista pública / visitante:** solo lectura, filtros por tipo de vacante, casos de proyecto, evidencia multimedia, CV ATS, Match de Vacante y cambio Español/English.
- **Vista administrador:** edición de contenido desde el navegador sin tocar Python, carga de foto, videos, PDFs e imágenes, creación/edición/eliminación de experiencias, proyectos, competencias, formación, certificaciones y evidencias.

## 1. Vista pública

La URL normal muestra únicamente el portafolio:

`https://TU-APP.streamlit.app/`

No hay botones de edición ni información de administración.

## 2. Vista administrador

Usa la misma URL agregando:

`?admin=1`

Ejemplo:

`https://TU-APP.streamlit.app/?admin=1`

La aplicación pedirá la contraseña definida en Streamlit Secrets.

## 3. Persistencia de datos

La app tiene dos modos:

### Local JSON
Funciona para pruebas. Los cambios se escriben a `profile_data.json`, pero en Streamlit Cloud pueden perderse cuando la instancia se reinicia.

### Supabase (recomendado)
Permite que todos los cambios hechos en el panel administrador queden guardados de forma persistente y también almacena fotos, videos, PDFs y evidencias.

### Crear la estructura en Supabase

1. Abre tu proyecto Supabase.
2. Ve a **SQL Editor**.
3. Copia y ejecuta todo el contenido de `supabase_setup.sql`.
4. Ve a **Project Settings > API** y copia:
   - Project URL
   - `service_role` key
5. No publiques la service-role key en GitHub.

## 4. Configurar Streamlit Secrets

En Streamlit Cloud:

1. Abre tu aplicación.
2. **Settings / App settings > Secrets**.
3. Agrega:

```toml
ADMIN_PASSWORD = "TU-CONTRASEÑA-PRIVADA"
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_SERVICE_KEY = "TU-SERVICE-ROLE-KEY"
SUPABASE_BUCKET = "portfolio-media"
```

Guarda y reinicia la app.

Hay un ejemplo en `.streamlit/secrets.toml.example`.

## 5. Idiomas

La versión maestra se edita en español.

En el administrador abre **Traducción EN** y pulsa:

**Generar / actualizar versión completa en inglés**

La app crea una segunda versión independiente para la vista pública en inglés. La traducción automática se debe revisar, especialmente cargos, términos técnicos y nombres propios.

## 6. Evidencias

En **Administrador > Evidencias** puedes publicar:

- fotografías,
- videos MP4,
- enlaces de YouTube/Vimeo,
- PDFs,
- certificaciones,
- cartas o reconocimientos,
- capturas de dashboards,
- documentación sanitizada.

No publiques contratos, RFC/CURP, datos personales, precios confidenciales, información protegida por NDA ni archivos internos sin autorización.

## 7. Archivos principales

- `app.py` — interfaz pública y administrador.
- `storage.py` — persistencia local/Supabase y archivos multimedia.
- `i18n.py` — textos de interfaz y traducción ES→EN.
- `profile_data.json` — respaldo/base española.
- `profile_data_en.json` — respaldo/base inglesa.
- `supabase_setup.sql` — tabla y bucket de almacenamiento.
- `requirements.txt` — dependencias.

## 8. Despliegue

En Streamlit Cloud usa:

- Repository: `ProjectmanagerAB/Abraham_Professional_Hub`
- Branch: `main`
- Main file path: `app.py`

Después configura los Secrets.
