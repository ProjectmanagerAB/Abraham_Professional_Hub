"""Local F5-TTS worker. Requires f5-tts, requests, ffmpeg and GPU recommended."""
import os, time, uuid, tempfile, subprocess, re
from pathlib import Path
import requests

URL=os.environ["SUPABASE_URL"].rstrip("/")
KEY=os.environ["SUPABASE_SERVICE_KEY"]
HEAD={"apikey":KEY,"Authorization":"Bearer "+KEY,"Content-Type":"application/json"}
def call(method,path,**kwargs):
    h=HEAD.copy()
    if "content_type" in kwargs: h["Content-Type"]=kwargs.pop("content_type")
    r=requests.request(method,URL+path,headers=h,timeout=180,**kwargs)
    r.raise_for_status()
    return r
def update(jid,**fields):
    call("PATCH","/rest/v1/voice_jobs",params={"id":"eq."+jid},json=fields)
def chunks(text,maxlen=350):
    sentences=re.split(r"(?<=[.!?])\s+",text.strip())
    out=[]; buf=""
    for sentence in sentences:
        for piece in [sentence[i:i+maxlen] for i in range(0,len(sentence),maxlen)]:
            if len(buf)+len(piece)+1>maxlen and buf:
                out.append(buf); buf=""
            buf=(buf+" "+piece).strip()
    if buf:out.append(buf)
    return out
def produce(tts,job):
    jid=job["id"]
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        reference=root/"reference.wav"
        reference.write_bytes(call("GET","/storage/v1/object/voice-private/"+job["reference_path"]).content)
        paths=[]
        for i,part in enumerate(chunks(job["script"])):
            wav=root/f"part_{i:04d}.wav"
            tts.infer(ref_file=str(reference),ref_text=job["reference_text"],gen_text=part,file_wave=str(wav))
            if not wav.exists():raise RuntimeError("El motor no generó WAV para el segmento "+str(i+1))
            paths.append(wav)
        concat=root/"concat.txt"
        concat.write_text("".join("file '"+str(p).replace("'","'\\''")+"'\n" for p in paths),encoding="utf-8")
        mp3=root/"episode.mp3"
        subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-codec:a","libmp3lame","-b:a","192k",str(mp3)],check=True,capture_output=True)
        output="episodes/"+jid+".mp3"
        call("POST","/storage/v1/object/voice-private/"+output,data=mp3.read_bytes(),content_type="audio/mpeg")
        update(jid,status="done",output_path=output,error=None)
def main():
    from f5_tts.api import F5TTS
    print("Cargando F5-TTS... La primera ejecución puede descargar modelos.")
    tts=F5TTS()
    print("Trabajador listo. Esperando episodios.")
    while True:
        try:
            jobs=call("GET","/rest/v1/voice_jobs",params={"select":"*","status":"eq.queued","order":"created_at.asc","limit":"1"}).json()
            if jobs:
                job=jobs[0]; jid=job["id"]
                # Single-worker design; do not start multiple workers simultaneously.
                update(jid,status="processing",error=None)
                try: produce(tts,job)
                except Exception as exc:
                    update(jid,status="failed",error=str(exc)[:900])
                    print("Fallo:",jid,exc)
            else:time.sleep(8)
        except KeyboardInterrupt:break
        except Exception as exc:
            print("Error de conexión:",exc);time.sleep(15)
if __name__=="__main__":main()
