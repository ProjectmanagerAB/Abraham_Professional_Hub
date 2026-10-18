"""Private admin-only voice studio. Never import from public routes."""
import io
import re
import uuid
import wave
import numpy as np
import requests
import streamlit as st

def _cfg():
    return str(st.secrets.get("SUPABASE_URL", "")).rstrip("/"), str(st.secrets.get("SUPABASE_SERVICE_KEY", ""))

def _request(method, path, **kwargs):
    url, key = _cfg()
    if not url or not key:
        raise RuntimeError("Falta configurar Supabase.")
    mime = kwargs.pop("mime", "application/json")
    response = requests.request(method, url + path, headers={"apikey":key,"Authorization":"Bearer "+key,"Content-Type":mime}, timeout=45, **kwargs)
    response.raise_for_status()
    return response

def _store_sample(blob):
    name = "references/" + uuid.uuid4().hex + ".wav"
    _request("POST", "/storage/v1/object/voice-private/" + name, data=blob, mime="audio/wav")
    return name

def _master_wav(blob, noise_reduction, trim_silence):
    """Lightweight speech mastering. No third-party voice service; no upload."""
    import noisereduce as nr
    with wave.open(io.BytesIO(blob), "rb") as reader:
        channels, rate, width, frames = reader.getnchannels(), reader.getframerate(), reader.getsampwidth(), reader.getnframes()
        if width != 2 or channels not in (1,2) or frames / max(rate,1) > 600:
            raise ValueError("Usa audio WAV PCM de 16 bits, mono/estéreo y máximo 10 minutos por toma.")
        raw = reader.readframes(frames)
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32).reshape(-1, channels) / 32768.0
    if channels == 2:
        data = data.mean(axis=1)
    else:
        data = data[:,0]
    if not len(data):
        raise ValueError("La grabación está vacía.")
    # Remove DC offset and apply a mild high-pass filter to reduce rumble.
    from scipy.signal import butter, sosfilt
    data -= np.mean(data)
    if rate > 200:
        data = sosfilt(butter(2, 75, btype="highpass", fs=rate, output="sos"), data).astype(np.float32)
    if noise_reduction:
        data = nr.reduce_noise(y=data, sr=rate, stationary=False, prop_decrease=0.65).astype(np.float32)
    if trim_silence:
        window = max(1, int(rate * 0.025))
        envelope = np.convolve(np.abs(data), np.ones(window, dtype=np.float32)/window, mode="same")
        threshold = max(float(np.max(envelope)) * 0.015, 0.001)
        indices = np.flatnonzero(envelope > threshold)
        if len(indices):
            pad = int(rate * 0.25)
            data = data[max(0,int(indices[0])-pad):min(len(data),int(indices[-1])+pad)]
    # Gentle peak normalization with 1 dB headroom; preserves expressive dynamics.
    peak = float(np.max(np.abs(data)))
    if peak > 1e-6:
        data = data * min(3.0, (10 ** (-1/20)) / peak)
    data = np.clip(data, -0.95, 0.95)
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(rate)
        writer.writeframes((data * 32767).astype("<i2").tobytes())
    return output.getvalue()

def render_voice_studio():
    st.header("🎙️ MI VOZ AI STUDIO")
    st.caption("Estudio personal y privado · Android · grabación y remasterización sin costo por uso")
    tabs = st.tabs(["🎚️ Grabar y mejorar", "🗣️ Clonación IA", "🎧 Episodios", "🎼 Música y mezclas", "⚙️ Ayuda"])
    with tabs[0]:
        st.subheader("Tu voz real, con sonido más limpio")
        st.info("Graba una sección de 3 a 5 minutos. Puedes repetir las tomas que necesites. El procesamiento se hace dentro de esta aplicación, sin enviar tu voz a una API de terceros.")
        with st.form("mastering_form"):
            name = st.text_input("Nombre de la toma", value="Jericó - Primera lectura")
            source = st.radio("Origen", ["Grabar desde Android", "Subir WAV"], horizontal=True)
            if source == "Grabar desde Android":
                audio = st.audio_input("Grabar lectura", sample_rate=24000)
            else:
                audio = st.file_uploader("Audio WAV (PCM 16 bits)", type=["wav"], key="master_upload")
            reduce_noise = st.checkbox("Reducir ruido de fondo", value=True)
            trim = st.checkbox("Recortar silencios al inicio y al final", value=True)
            submit = st.form_submit_button("✨ Mejorar mi grabación", use_container_width=True)
        if submit:
            if not audio:
                st.error("Graba o selecciona una toma primero.")
            elif len(audio.getvalue()) > 35 * 1024 * 1024:
                st.error("La toma supera 35 MB. Graba una sección más corta.")
            else:
                try:
                    with st.spinner("Limpiando y normalizando tu voz..."):
                        processed = _master_wav(audio.getvalue(), reduce_noise, trim)
                    st.session_state["mastered_audio"] = processed
                    st.session_state["mastered_name"] = name.strip() or "Mi_voz"
                    st.success("Toma procesada. Escúchala antes de descargar.")
                except Exception as exc:
                    st.error("No se pudo procesar: " + str(exc))
        if st.session_state.get("mastered_audio"):
            st.audio(st.session_state["mastered_audio"], format="audio/wav")
            filename = re.sub(r"[^a-zA-Z0-9_-]+", "_", st.session_state.get("mastered_name", "Mi_voz"))
            st.download_button("⬇️ Descargar audio limpio WAV", st.session_state["mastered_audio"], file_name=filename+".wav", mime="audio/wav", use_container_width=True)
            st.caption("Guarda cada toma descargada. Este primer procesador no almacena automáticamente los archivos ni une capítulos.")
    with tabs[1]:
        st.warning("La clonación IA sigue en fase de preparación: enviar un trabajo no genera audio hasta conectar un motor.")
        url, key = _cfg()
        if not url or not key:
            st.error("Falta configurar Supabase para la cola de clonación.")
        else:
            with st.form("voice_job"):
                title = st.text_input("Título del episodio", max_chars=150)
                script = st.text_area("Guion completo", height=260, max_chars=100000)
                source = st.radio("Muestra de voz", ["Grabar con Android", "Subir archivo WAV"], horizontal=True)
                sample = st.audio_input("Toca para grabar tu voz", sample_rate=24000, key="clone_sample") if source == "Grabar con Android" else st.file_uploader("Selecciona WAV", type=["wav"], key="clone_upload")
                transcript = st.text_area("Transcripción exacta de la muestra")
                consent = st.checkbox("Confirmo que es mi propia voz o tengo autorización expresa.")
                submitted = st.form_submit_button("Enviar a cola de clonación", use_container_width=True)
            st.caption(f"{len(script.split())} palabras · duración estimada {len(script.split())/130:.1f} minutos")
            if submitted:
                if not title.strip() or not script.strip() or not transcript.strip() or not sample or not consent:
                    st.error("Completa título, guion, muestra, transcripción y consentimiento.")
                elif len(sample.getvalue()) > 15 * 1024 * 1024:
                    st.error("La muestra supera 15 MB.")
                else:
                    try:
                        path = _store_sample(sample.getvalue())
                        _request("POST", "/rest/v1/voice_jobs", params={"select":"id"}, json={"title":title.strip(),"script":script.strip(),"reference_path":path,"reference_text":transcript.strip(),"status":"queued"})
                        st.success("Trabajo guardado en cola. Pendiente de activar el motor de clonación.")
                    except Exception as exc:
                        st.error("Error al guardar trabajo: " + str(exc))
    with tabs[2]:
        url, key = _cfg()
        if not url or not key:
            st.info("El historial de clonación requiere Supabase.")
        else:
            if st.button("🔄 Actualizar episodios", use_container_width=True):
                st.rerun()
            try:
                jobs = _request("GET", "/rest/v1/voice_jobs", params={"select":"id,title,status,output_path,error,created_at","order":"created_at.desc","limit":"30"}).json()
                if not jobs:
                    st.info("Todavía no hay trabajos.")
                for job in jobs:
                    with st.expander(job["title"] + " · " + job["status"]):
                        st.caption(str(job["created_at"]))
                        if job.get("error"):
                            st.error(job["error"])
                        if job["status"] == "done" and job.get("output_path"):
                            result = _request("GET", "/storage/v1/object/voice-private/" + job["output_path"]).content
                            st.audio(result, format="audio/mpeg")
                            st.download_button("Descargar MP3", result, file_name=re.sub(r"[^a-zA-Z0-9_-]+","_",job["title"])+".mp3", mime="audio/mpeg", key="download_"+job["id"], use_container_width=True)
            except Exception as exc:
                st.error("No se pudo consultar el historial: " + str(exc))
    with tabs[3]:
        from audio_music_module import render_music_studio
        render_music_studio()
    with tabs[4]:
        st.markdown("**Primera enseñanza: La caída de los muros de Jericó.** Abre Grabar y mejorar, lee una sección de tu guion y pulsa Mejorar mi grabación. Repite por capítulos.")
        st.info("Este primer modo procesa WAV PCM de 16 bits hasta 10 minutos por toma. Elimina ruido moderado, filtra graves, normaliza volumen y recorta solo extremos. No corrige palabras ni reemplaza la interpretación.")
        st.warning("El archivo limpio se entrega en WAV, no MP3. Guarda las tomas antes de cerrar la pestaña. La unión de capítulos y exportación MP3 quedan pendientes.")
