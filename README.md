# Abraham Professional Hub · CV y portafolio profesional

Aplicación pública de portafolio profesional desarrollada en Streamlit.

## Funcionalidades

- Trayectoria profesional y proyectos seleccionados.
- Experiencia, habilidades, formación y certificaciones.
- Evidencias multimedia publicadas.
- Vista en español e inglés.
- Descarga de CV ATS y comparador de vacantes.
- Enlaces profesionales y contacto por WhatsApp.
- Formulario de respuesta para reclutadores (requiere almacenamiento configurado).

## Cambios de esta versión

Se eliminó del flujo de la aplicación la ruta `?admin=1`, el panel de edición y el acceso a MI VOZ AI STUDIO. La aplicación ahora presenta exclusivamente la vista pública. La conexión existente a Supabase puede mantenerse para lectura del perfil y registro de respuestas de reclutadores. **No se han eliminado datos de Supabase ni archivos históricos del repositorio.**

## Despliegue

En Streamlit Community Cloud:

- Repositorio: `ProjectmanagerAB/Abraham_Professional_Hub`
- Rama: `main`
- Archivo principal: `app.py`

Las claves de Supabase, si se requieren, deben permanecer en los secretos privados de Streamlit Cloud y nunca publicarse en GitHub. No es necesario configurar `ADMIN_PASSWORD` para esta versión.

## Archivos de contenido

- `app.py`: portafolio público.
- `storage.py`: lectura del perfil y gestión de respuestas.
- `profile_data.json` y `profile_data_en.json`: respaldo local de datos del CV.
- `career_utils.py`: historial profesional complementario.
- `i18n.py`: interfaz bilingüe.
