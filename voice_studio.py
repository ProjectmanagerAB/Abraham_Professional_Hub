"""Private admin-only podcast UI. Never import from public routes."""
import io
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
    tabs = st.tabs(["Crear episodio", "Mis producciones", "Instalación"])
    with tabs[0]:
        with st.form("voice_job"):
            title = st.text_input("Título del episodio", max_chars=150)
            script = st.text_area("Guion completo", height=260, max_chars=100000)
            sample = st.file_uploader("Muestra limpia de tu propia voz (WAV)", type=["wav"])
            transcript = st.text_area("Transcripción exacta de lo que dices en la muestra", height=85)
            consent = st.checkbox("Confirmo que es mi propia voz o que tengo autorización expresa para clonarla.")
            submitted = st.form_submit_button("Enviar a producción", use_container_width=True)
        st.caption("El audio se produce en tu computadora cuando el trabajador F5-TTS está ejecutándose. Una muestra de 10–20 segundos con transcripción precisa suele ser un buen punto de partida.")
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
        if st.button("Actualizar lista", key="voice_refresh"):
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
                        st.download_button("Descargar MP3", audio, file_name=re.sub(r"[^a-zA-Z0-9_-]+", "_", job["title"]) + ".mp3", mime="audio/mpeg", key="download_"+job["id"])
        except Exception as exc:
            st.error("Error consultando trabajos: " + str(exc))
    with tabs[2]:
        st.info("Ejecuta voice_worker.py en tu computadora con F5-TTS y FFmpeg instalados. Consulta VOICE_STUDIO_SETUP.md.")
        st.warning("No publiques la service-role key. El bucket voice-private debe permanecer privado.")
