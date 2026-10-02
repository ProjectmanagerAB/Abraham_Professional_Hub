# Abraham Professional Hub

Portafolio profesional interactivo construido en Streamlit para presentar una trayectoria adaptable a distintas vacantes: Project Management, Operations, Production, Plant/Manufacturing, PMO y Supply Chain/Logistics.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estructura

- `app.py` — aplicación principal.
- `profile_data.json` — contenido profesional maestro, separado del código.
- `assets/profile.jpg` — fotografía profesional. Si no existe, la app muestra las iniciales AY.
- `requirements.txt` — dependencias.

## Secciones

- Inicio ejecutivo con selector de enfoque profesional.
- Trayectoria filtrada por tipo de vacante.
- Casos de proyecto.
- Competencias y palabras clave.
- Formación y credenciales.
- Evidencias profesionales sanitizadas.
- Match de vacante por similitud textual.
- CV ATS descargable por enfoque.
- Panel Admin para futuras cargas y actualización de contenido.

## Publicación rápida

1. Sube esta carpeta a un repositorio privado o público en GitHub.
2. Conecta el repositorio con Streamlit Community Cloud.
3. Define `app.py` como archivo de entrada.
4. Publica y comparte el enlace.

## Antes de publicar

Completar:
- foto profesional (`assets/profile.jpg`);
- instituciones de Ingeniería y Maestría;
- nivel de inglés;
- certificaciones verificadas;
- métricas cuantitativas de proyectos cuando sean demostrables;
- evidencias sanitizadas.

No publicar contratos completos, cuentas bancarias, identificaciones, firmas, precios sensibles, información de terceros ni documentos cubiertos por NDA.
