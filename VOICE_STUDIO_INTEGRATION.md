# MI VOZ AI STUDIO — Integración privada (fase 1)

Repositorio base: Abraham_Professional_Hub. Rama de trabajo: feature/private-voice-studio-v1.

## Hallazgos
- app.py contiene el acceso de administrador mediante ?admin=1 y contraseña ADMIN_PASSWORD.
- La vista pública se ejecuta fuera de esa rama de autenticación.
- storage.py utiliza el bucket público portfolio-media. **No almacenar voces ni podcasts privados en ese bucket.**
- El motor F5-TTS requiere servicio separado con recursos adecuados y autenticación.

## Integración propuesta (NO aplicada a app.py)
1. Dentro del bloque autenticado `if is_admin_route():`, después de validar `admin_authenticated()`, importar `render_voice_studio` desde `voice_studio.py`.
2. Agregar "MI VOZ AI STUDIO" a las opciones del radio `section = st.sidebar.radio("Administración", ...)`.
3. Añadir `if section == "MI VOZ AI STUDIO": render_voice_studio()` dentro de la rama de administrador.
4. Crear un bucket Supabase **privado** para muestras y audio, con rutas de acceso firmadas de corta duración y controles de acceso del lado del servidor.
5. Conectar un worker privado de F5-TTS; proteger solicitudes, establecer cuotas, controlar consentimiento y exportar WAV/MP3.
6. Probar que la vista pública no expone el módulo, que las rutas privadas exigen autorización y que el despliegue conserva su comportamiento.

La presente rama incluye el módulo de interfaz aislado y esta guía, sin tocar la aplicación pública ni desplegar cambios.
