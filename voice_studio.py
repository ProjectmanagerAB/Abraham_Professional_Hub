"""Private admin-only podcast UI. Never import from public routes."""
import re
import uuid
import requests
import streamlit as st

def _cfg():
    url = str(st.secrets.get("SUPABASE_URL", "")).rstrip("/")
    key = str(st.secrets.get("SUPABASE_SERVICE_KEY", ""))
    return url, key

def _headers(mime="application/json"):
    _, key = _cfg()
    return {"apikey": key, "Authorization": "Bearer " + key, "Content-Type": mime}

def _request(method, path, **kwargs):
    url, key = _cfg()
    if not url or not key:
        raise RuntimeError("Falta configurar Supabase.")
    r = requests.request(method, url + path, headers=_headers(kwargs.pop("mime", "application/json")), timeout=45, **kwargs)
    r.raise_for_status()
    return r

def _store_sample(blob):
    name = "references/" + uuid.uuid4().hex + ".wav"
    _request("POST", "/storage/v1/object/voice-private/" + name, data=blob, mime="audio/wav")
    return name

def render_voice_studio():
    st.header("🎙️ MI VOZ AI STUDIO")
    st.caption("Módulo privado · F5-TTS local · producción por cola segura")
    url, key = _cfg()
    if not url or not key:
        st.error("Configura SUPABASE_URL y SUPABASE_SERVICE_KEY para activar el estudio.")
        return
    tabs = st.tabs(["🎙️ Crear", "🎧 Episodios", "⚙️ Ayuda"])
    with tabs[0]:
        with st.form("voice_job"):
            title = st.text_input("Título del episodio", max_chars=150)
            script = st.text_area("Guion completo", height=260, max_chars=100000)
            source = st.radio("Muestra de voz", ["Grabar con Android", "Subir archivo WAV"], horizontal=True)
            if source == "Grabar con Android":
                sample = st.audio_input("Toca para grabar tu voz", sample_rate=24000)
            else:
                sample = st.file_uploader("Selecciona tu archivo WAV", type=["wav"])
            transcript = st.text_area("Transcripción exacta de lo que dices en la muestra", height=85)
            consent = st.checkbox("Confirmo que es mi propia voz o que tengo autorización expresa para clonarla.")
            submitted = st.form_submit_button("🎙️ Enviar a producción", use_container_width=True)
        st.caption(f"{len(script.split())} palabras · duración estimada {len(script.split()) / 130:.1f} minutos.")
        st.info("Puedes cerrar Chrome tras enviar el trabajo. Windows lo procesará cuando el motor esté encendido.")
        if submitted:
            if not title.strip() or not script.strip() or not transcript.strip() or not sample or not consent:
                st.error("Completa título, guion, muestra, transcripción y consentimiento.")
            elif len(sample.getvalue()) > 15 * 1024 * 1024:
                st.error("La muestra no debe superar 15 MB.")
            else:
                try:
                    sample_path = _store_sample(sample.getvalue())
                    payload = {"title": title.strip(), "script": script.strip(), "reference_path": sample_path, "reference_text": transcript.strip(), "status": "queued"}
                    _request("POST", "/rest/v1/voice_jobs", params={"select":"id"}, json=payload)
                    st.success("Trabajo enviado. Abre Mis producciones para consultar el avance.")
                except Exception as exc:
                    st.error("No se pudo crear el trabajo: " + str(exc))
    with tabs[1]:
        if st.button("🔄 Actualizar episodios", key="voice_refresh", use_container_width=True):
            st.rerun()
        try:
            jobs = _request("GET", "/rest/v1/voice_jobs", params={"select":"id,title,status,output_path,error,created_at","order":"created_at.desc","limit":"30"}).json()
            if not jobs:
                st.info("Todavía no hay producciones.")
            for job in jobs:
                with st.expander(job["title"] + " · " + job["status"]):
                    st.caption(str(job["created_at"]))
                    if job.get("error"):
                        st.error(job["error"])
                    if job["status"] == "done" and job.get("output_path"):
                        audio = _request("GET", "/storage/v1/object/voice-private/" + job["output_path"]).content
                        st.audio(audio, format="audio/mpeg")
                        st.download_button("Descargar MP3", audio, file_name=re.sub(r"[^a-zA-Z0-9_-]+", "_", job["title"]) + ".mp3", mime="audio/mpeg", key="download_"+job["id"], use_container_width=True)
        except Exception as exc:
            st.error("Error consultando trabajos: " + str(exc))
    with tabs[2]:
        st.info("Android: graba, pega el guion y envía. Windows: mantén abierto voice_worker.py con F5-TTS y FFmpeg. Consulta VOICE_STUDIO_SETUP.md.")
        st.warning("No publiques la service-role key. El bucket voice-private debe permanecer privado.")
