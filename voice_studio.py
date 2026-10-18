"""Private voice studio UI. Import and call ONLY after admin authentication."""
import streamlit as st

def render_voice_studio():
    st.header("🎙️ MI VOZ AI STUDIO")
    st.caption("Área privada · Preparación de guiones y muestras de voz")
    st.info("La generación con F5-TTS requiere un trabajador privado externo con GPU. No se ejecuta en Streamlit Cloud.")
    tab1, tab2, tab3 = st.tabs(["Guiones", "Mi voz", "Producción"])
    with tab1:
        title = st.text_input("Título del episodio", key="voice_episode_title")
        script = st.text_area("Guion", height=300, key="voice_script")
        st.caption(f"{len(script.split())} palabras · aproximadamente {len(script.split())/130:.1f} minutos a 130 palabras/minuto")
        st.download_button("Descargar guion TXT", data=script, file_name="guion_podcast.txt", mime="text/plain", disabled=not script.strip())
    with tab2:
        st.warning("Usa únicamente grabaciones de tu propia voz o de una persona que haya dado su consentimiento.")
        recording = st.audio_input("Graba una muestra de tu voz")
        if recording:
            st.audio(recording)
            st.download_button("Descargar muestra WAV", recording.getvalue(), "muestra_voz.wav", "audio/wav")
        st.caption("No guardamos automáticamente la muestra en el repositorio ni en el bucket público del portafolio.")
    with tab3:
        st.write("Motor seleccionado: F5-TTS local")
        st.warning("Generación de audio pendiente de conectar a un servicio privado autenticado y almacenamiento no público.")
        st.caption("No se enviarán grabaciones a un servicio externo hasta que esté configurado y autorizado.")
