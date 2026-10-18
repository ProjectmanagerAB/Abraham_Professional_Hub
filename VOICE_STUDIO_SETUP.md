# MI VOZ AI STUDIO · Instalación del motor privado

1. Ejecuta `voice_studio_setup.sql` en el SQL Editor del proyecto Supabase que ya utiliza Abraham Professional Hub.
2. Mantén `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` existentes en Streamlit Secrets. No los copies a GitHub ni al navegador.
3. En la computadora que procesará audio, instala Python compatible con F5-TTS, FFmpeg y (preferiblemente) una GPU NVIDIA con PyTorch compatible.
4. Crea un entorno virtual e instala: `pip install f5-tts requests`.
5. Configura en las variables de entorno del sistema `SUPABASE_URL` y `SUPABASE_SERVICE_KEY`. Para reducir riesgo, idealmente usa una credencial específica de worker con permisos mínimos; el prototipo reutiliza la service-role key y requiere proteger estrictamente esa computadora.
6. Ejecuta `python voice_worker.py`. Déjalo abierto mientras generas audios.
7. En la app web abre `?admin=1`, inicia sesión, elige MI VOZ AI STUDIO, graba o carga un WAV y escribe exactamente las palabras de la muestra. Pega el guion y pulsa Enviar a producción.
8. En Mis producciones, actualiza y descarga el MP3 cuando el estado sea done.

## Limitaciones y seguridad
- El módulo solo aparece dentro de la rama de administrador autenticado. La ruta `?admin=1` no es una barrera de seguridad por sí sola: la contraseña sí.
- El worker usa polling saliente a Supabase; no se abre ningún puerto entrante en tu computadora.
- El bucket privado nunca debe convertirse en público.
- La cola está diseñada para un único worker; antes de usar varios se requiere reclamación atómica.
- Las muestras WAV se almacenan de manera privada pero todavía no hay eliminación automática ni gestión de retención.
- La calidad y el tiempo de síntesis dependen del hardware y de la instalación del modelo. Verifica localmente las APIs de F5-TTS, que pueden cambiar entre versiones.
- Los MP3 son descargables desde el administrador. No existe publicación automática en redes sociales.
- No se ha ejecutado una prueba de síntesis de extremo a extremo desde este entorno.
