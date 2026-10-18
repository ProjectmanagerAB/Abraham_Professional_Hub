"""Módulo ligero de producción musical para MI VOZ AI STUDIO."""
import io, wave, shutil, tempfile, subprocess, sys
from pathlib import Path
import numpy as np
import streamlit as st
from scipy.signal import resample_poly
from math import gcd

def decode(blob,name):
    if len(blob)>35*1024*1024: raise ValueError("Límite 35 MB")
    if name.lower().endswith(".wav"):
        with wave.open(io.BytesIO(blob),"rb") as w:
            if w.getsampwidth()!=2:raise ValueError("Requiere WAV PCM 16-bit")
            rate=w.getframerate();channels=w.getnchannels()
            if channels not in (1,2) or w.getnframes()/rate>600:raise ValueError("Máximo 10 minutos, mono o estéreo")
            y=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").astype(np.float32).reshape(-1,channels).mean(axis=1)/32768
    else:
        if not shutil.which("ffmpeg"):raise ValueError("MP3 requiere FFmpeg en el servidor; sube WAV de 16 bits")
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/("input"+Path(name).suffix.lower());path.write_bytes(blob)
            result=subprocess.run(["ffmpeg","-nostdin","-v","error","-i",str(path),"-t","600","-ar","24000","-ac","1","-f","s16le","pipe:1"],capture_output=True,timeout=120)
            if result.returncode:raise ValueError("No se pudo decodificar")
            return np.frombuffer(result.stdout,dtype="<i2").astype(np.float32)/32768
    if rate!=24000:y=resample_poly(y,24000//gcd(rate,24000),rate//gcd(rate,24000)).astype(np.float32)
    return y

def encode(y):
    b=io.BytesIO()
    with wave.open(b,"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000)
        w.writeframes((np.clip(y,-.99,.99)*32767).astype("<i2").tobytes())
    return b.getvalue()

def render_music_studio():
    st.subheader("🎼 Producción musical y narrativa")
    st.caption("Módulo privado. Sin APIs de pago; procesamiento de mezcla dentro de la aplicación.")
    a,b,c=st.tabs(["🎙️ Voz + música","🎚️ Mezclador","✂️ Separar instrumentos"])
    with a:
        use_previous=bool(st.session_state.get("mastered_audio"))
        if use_previous: previous=st.checkbox("Usar la última grabación mejorada",value=True)
        else:previous=False
        voice=None if previous else st.file_uploader("Narración",type=["wav","mp3","m4a"],key="music_voice")
        music=st.file_uploader("Música de fondo",type=["wav","mp3","m4a"],key="music_bg")
        level=st.slider("Volumen de fondo (%)",0,60,12)
        duck=st.checkbox("Bajar música mientras hablo",True)
        if st.button("Crear narración con música",disabled=(music is None or (not previous and voice is None))):
            try:
                v=decode(st.session_state["mastered_audio"],"voz.wav") if previous else decode(voice.getvalue(),voice.name)
                m=decode(music.getvalue(),music.name)
                if not len(v) or not len(m):raise ValueError("Archivo vacío")
                m=np.tile(m,int(np.ceil(len(v)/len(m))))[:len(v)]
                if duck:
                    from scipy.ndimage import uniform_filter1d
                    env=np.where(uniform_filter1d(v*v,size=4800)>0.00004,.35,1)
                else:env=np.ones(len(v))
                mixed=v+m*level/100*env
                peak=np.max(np.abs(mixed))
                if peak>.98:mixed*=.98/peak
                st.session_state["narration_music_result"]=encode(mixed)
            except Exception as e:st.error(str(e))
        if st.session_state.get("narration_music_result"):
            wav=st.session_state["narration_music_result"];st.audio(wav,format="audio/wav")
            st.download_button("Descargar narración mezclada",wav,file_name="narracion_musical.wav",mime="audio/wav")
    with b:
        files=st.file_uploader("Sube hasta 6 pistas",type=["wav","mp3","m4a"],accept_multiple_files=True,key="music_tracks")
        if files and len(files)<=6:
            gains=[st.slider(f.name,0,150,100,key="track_gain_"+str(i))/100 for i,f in enumerate(files)]
            if st.button("Generar mezcla"):
                try:
                    tracks=[decode(f.getvalue(),f.name) for f in files]
                    n=min(map(len,tracks))
                    if not n:raise ValueError("Pistas vacías")
                    mixed=sum((t[:n]*g for t,g in zip(tracks,gains)),np.zeros(n,dtype=np.float32))
                    peak=np.max(np.abs(mixed))
                    if peak>.98:mixed*=.98/peak
                    st.session_state["music_mix_result"]=encode(mixed)
                except Exception as e:st.error(str(e))
        elif files:st.warning("Máximo 6 pistas")
        if st.session_state.get("music_mix_result"):
            wav=st.session_state["music_mix_result"];st.audio(wav,format="audio/wav")
            st.download_button("Descargar mezcla",wav,file_name="mezcla.wav",mime="audio/wav")
    with c:
        st.info("La separación IA requiere Demucs y FFmpeg instalados en el servidor; no consume API de pago pero exige recursos.")
        try:
            import importlib.util
            ready=importlib.util.find_spec("demucs") is not None and shutil.which("ffmpeg") is not None
        except Exception:ready=False
        if not ready:
            st.warning("El motor Demucs no está instalado aquí. La mezcla y la narración funcionan sin él.")
        else:
            song=st.file_uploader("Canción",type=["wav","mp3","m4a"],key="music_separate")
            if st.button("Separar voz, batería, bajo y otros",disabled=not song):
                try:
                    blob=song.getvalue()
                    if len(blob)>35*1024*1024:raise ValueError("Máximo 35 MB")
                    with tempfile.TemporaryDirectory() as tmp:
                        root=Path(tmp);path=root/("cancion"+Path(song.name).suffix.lower());path.write_bytes(blob)
                        with st.spinner("Procesando canción"):
                            p=subprocess.run([sys.executable,"-m","demucs","-n","htdemucs","-o",str(root/"out"),str(path)],capture_output=True,text=True,timeout=1200)
                        if p.returncode:raise RuntimeError(p.stderr[-700:])
                        st.session_state["music_stems"]={x.stem:x.read_bytes() for x in (root/"out"/"htdemucs"/"cancion").glob("*.wav")}
                except Exception as e:st.error(str(e))
            for name,blob in st.session_state.get("music_stems",{}).items():
                st.write(name);st.audio(blob,format="audio/wav")
                st.download_button("Descargar "+name,blob,file_name=name+".wav",key="music_stem_"+name)
