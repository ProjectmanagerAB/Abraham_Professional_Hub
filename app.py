import json
import re
from pathlib import Path
from datetime import datetime
import streamlit as st

BASE = Path(__file__).parent
DATA_FILE = BASE / "profile_data.json"
ASSETS = BASE / "assets"
PHOTO_FILE = ASSETS / "profile.jpg"

st.set_page_config(
    page_title="Abraham Yañez | Professional Hub",
    page_icon="AY",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { --radius: 20px; }
.block-container {max-width: 1240px; padding-top: 1.1rem; padding-bottom: 4rem;}
[data-testid="stSidebar"] {border-right:1px solid rgba(128,128,128,.16)}
.hero {padding: 2.15rem 2.35rem; border: 1px solid rgba(128,128,128,.22); border-radius: 26px; margin-bottom: 1rem;
       background: linear-gradient(135deg, rgba(30,55,88,.08), rgba(128,128,128,.025));}
.hero h1 {font-size: 2.75rem; line-height:1.04; margin: 0 0 .4rem 0; letter-spacing:-.04em;}
.hero .sub {font-size:1.06rem; opacity:.82; margin-bottom:.9rem;}
.hero p {font-size: 1.03rem; line-height: 1.68; max-width: 900px;}
.pill {display:inline-block; border:1px solid rgba(128,128,128,.32); border-radius:999px; padding:.30rem .72rem; margin:.15rem .18rem .15rem 0; font-size:.84rem;}
.card {border:1px solid rgba(128,128,128,.22); border-radius:20px; padding:1.05rem 1.15rem; margin-bottom:.85rem;}
.card-title {font-size:1.08rem; font-weight:700; margin-bottom:.18rem;}
.kicker {font-size:.78rem; letter-spacing:.11em; text-transform:uppercase; opacity:.62; font-weight:700;}
.muted {opacity:.70}.tiny {font-size:.78rem}.small {font-size:.88rem}
.stat {border:1px solid rgba(128,128,128,.20); border-radius:18px; padding:1rem; min-height:105px;}
.stat .v {font-size:1.13rem; font-weight:750; margin-top:.35rem;}
.timeline {border-left:2px solid rgba(128,128,128,.22); padding-left:1.1rem; margin-left:.35rem;}
.timeline-item {margin:0 0 1.35rem 0; position:relative;}
.timeline-item:before {content:""; width:10px; height:10px; border-radius:50%; background:currentColor; position:absolute; left:-1.48rem; top:.42rem; opacity:.55;}
.case {border:1px solid rgba(128,128,128,.22); border-radius:20px; padding:1rem 1.15rem; height:100%;}
.fit-good {border-left:5px solid #2e8b57; padding-left:.85rem}.fit-mid {border-left:5px solid #c28b18; padding-left:.85rem}.fit-low {border-left:5px solid #8b8b8b; padding-left:.85rem}
div[data-testid="stMetric"] {border:1px solid rgba(128,128,128,.18); padding:.8rem .9rem; border-radius:16px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def tokenize(text):
    return set(re.findall(r"[a-záéíóúñ0-9\+\#\.]{3,}", text.lower()))

def track_text(data, track):
    chunks = [data["profile_tracks"][track]["tagline"], " ".join(data["profile_tracks"][track]["keywords"])]
    for e in data["experience"]:
        if track in e.get("tracks", []):
            chunks += [e["role"], e["company"], " ".join(e["bullets"])]
    for p in data["projects"]:
        if track in p.get("tracks", []):
            chunks += [p["title"], p["sector"], p["summary"]]
    for values in data["skills"].values():
        chunks.append(" ".join(values))
    return " ".join(chunks)

def build_ats(data, track):
    p = data["personal"]
    selected_exp = [e for e in data["experience"] if track in e.get("tracks", [])]
    selected_projects = [x for x in data["projects"] if track in x.get("tracks", [])]
    keys = data["profile_tracks"][track]["keywords"]
    out = [
        p["name"].upper(), track.upper(),
        f"{p['location']} | {p['email']} | {p['phone']} | {p['linkedin']}", "",
        "PROFESSIONAL SUMMARY", p["summary"], "",
        "CORE SKILLS", " | ".join(keys), "", "EXPERIENCE"
    ]
    for e in selected_exp:
        out.append(f"{e['role']} | {e['company']} | {e['period']} | {e['location']}")
        out += ["- " + x for x in e["bullets"]]
        out.append("")
    out.append("SELECTED PROJECTS")
    for pr in selected_projects[:5]:
        out.append(f"- {pr['title']} | {pr['role']} | {pr['summary']}")
    out += ["", "EDUCATION"]
    for ed in data["education"]:
        inst = f" | {ed['institution']}" if ed.get("institution") else ""
        out.append(f"- {ed['degree']}{inst}")
    out += ["", "TOOLS & METHODS"]
    flat = []
    for vals in data["skills"].values():
        flat += vals
    out.append(" | ".join(dict.fromkeys(flat)))
    return "\n".join(out)

data = load_data()
p = data["personal"]
tracks = list(data["profile_tracks"].keys())

with st.sidebar:
    st.markdown("### Abraham Yañez")
    st.caption("Professional Hub")
    track = st.selectbox("Enfoque profesional", tracks, index=0)
    st.caption(data["profile_tracks"][track]["tagline"])
    st.divider()
    section = st.radio(
        "Navegación",
        ["Inicio", "Trayectoria", "Casos de proyecto", "Competencias", "Formación", "Evidencias", "Match de vacante", "CV ATS", "Admin"],
        label_visibility="collapsed",
    )
    st.divider()
    st.link_button("LinkedIn", p["linkedin"], use_container_width=True)
    st.caption("Portafolio público: sólo información profesional y evidencia sanitizada.")

keywords = data["profile_tracks"][track]["keywords"]

if section == "Inicio":
    left, right = st.columns([3.3, 1], gap="large")
    with left:
        st.markdown(f"""
        <div class="hero">
          <div class="kicker">Professional Portfolio</div>
          <h1>{p['name']}</h1>
          <div class="sub"><b>{p['headline']}</b></div>
          <p>{p['summary']}</p>
          <div>{''.join(f'<span class="pill">{k}</span>' for k in keywords)}</div>
        </div>
        """, unsafe_allow_html=True)
        b1, b2, b3 = st.columns(3)
        b1.link_button("Ver LinkedIn", p["linkedin"], use_container_width=True)
        b2.download_button("Descargar CV ATS", build_ats(data, track).encode("utf-8"), file_name=f"Abraham_Yanez_{track.replace(' ','_').replace('/','-')}.txt", use_container_width=True)
        b3.button("Disponible para oportunidades", use_container_width=True, disabled=True)
    with right:
        if PHOTO_FILE.exists():
            st.image(str(PHOTO_FILE), use_container_width=True)
        else:
            st.markdown("""
            <div class="card" style="text-align:center;padding:2.2rem .8rem">
              <div style="font-size:3.2rem;font-weight:800;letter-spacing:-.08em">AY</div>
              <div class="muted small">Foto profesional pendiente</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f"**{p['location']}**")
        st.caption(p["mobility"])

    st.markdown("### Perfil enfocado")
    st.write(data["profile_tracks"][track]["tagline"])
    c1, c2, c3, c4 = st.columns(4)
    for col, item in zip([c1,c2,c3,c4], data["highlights"]):
        col.markdown(f"<div class='stat'><div class='kicker'>{item['label']}</div><div class='v'>{item['value']}</div></div>", unsafe_allow_html=True)

    st.markdown("### Lo que puede demostrar")
    exp = [e for e in data["experience"] if track in e.get("tracks", [])][:3]
    cols = st.columns(max(1, len(exp)))
    for col, e in zip(cols, exp):
        col.markdown(f"<div class='case'><div class='kicker'>{e['period']}</div><div class='card-title'>{e['role']}</div><div class='muted small'>{e['company']}</div><br><div class='small'>{e['bullets'][0]}</div></div>", unsafe_allow_html=True)

elif section == "Trayectoria":
    st.header(f"Trayectoria · {track}")
    exp = [e for e in data["experience"] if track in e.get("tracks", [])] or data["experience"]
    st.markdown("<div class='timeline'>", unsafe_allow_html=True)
    for e in exp:
        st.markdown("<div class='timeline-item'>", unsafe_allow_html=True)
        st.subheader(f"{e['role']} · {e['company']}")
        st.caption(f"{e['period']} · {e['location']}")
        for b in e["bullets"]:
            st.write("• " + b)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif section == "Casos de proyecto":
    st.header("Casos de proyecto")
    st.caption("Pensados para demostrar alcance, criterio, ejecución y resultados; nunca para publicar contratos o información sensible.")
    projects = [x for x in data["projects"] if track in x.get("tracks", [])]
    if not projects:
        projects = data["projects"]
    for i in range(0, len(projects), 2):
        cols = st.columns(2)
        for col, pr in zip(cols, projects[i:i+2]):
            with col:
                st.markdown(f"<div class='case'><div class='kicker'>{pr['sector']} · {pr['region']}</div><div class='card-title'>{pr['title']}</div><div class='small'><b>Rol:</b> {pr['role']} &nbsp; <b>Estado:</b> {pr['status']}</div><br><div>{pr['summary']}</div><br><div class='muted tiny'>{pr['evidence_note']}</div></div>", unsafe_allow_html=True)
                with st.expander("Estructura del caso"):
                    st.write("**Contexto** — qué problema u oportunidad existía.")
                    st.write("**Responsabilidad** — qué parte estuvo bajo tu coordinación.")
                    st.write("**Acciones** — decisiones, planeación, coordinación y ejecución.")
                    st.write("**Resultado** — métricas, ahorro, capacidad, tiempo, calidad o continuidad.")
                    st.write("**Evidencia** — fotos, dashboard, carta, captura o documento sanitizado.")

elif section == "Competencias":
    st.header(f"Competencias · {track}")
    for area, skills in data["skills"].items():
        st.markdown(f"### {area}")
        st.markdown(" ".join([f"`{s}`" for s in skills]))
    st.divider()
    st.markdown("### Palabras clave del perfil")
    st.markdown(" ".join([f"`{s}`" for s in keywords]))

elif section == "Formación":
    st.header("Formación y credenciales")
    for e in data["education"]:
        st.markdown(f"### {e['degree']}")
        if e.get("institution"):
            st.write(e["institution"])
        else:
            st.caption("Institución pendiente de incorporar")
        st.caption(e["credential"])
    st.divider()
    st.subheader("Certificaciones y membresías")
    for c in data["certifications"]:
        st.write(f"**{c['name']}** — {c['status']}")

elif section == "Evidencias":
    st.header("Evidencias profesionales")
    st.write("Aquí aparecerán fotografías, videos, reconocimientos, cartas y documentos públicos o sanitizados.")
    if data.get("evidence"):
        for ev in data["evidence"]:
            st.markdown(f"- {ev}")
    else:
        st.info("La estructura ya está lista. La siguiente carga será tu fotografía profesional y evidencia seleccionada por proyecto.")
    st.warning("No publicar: contratos completos, precios sensibles, datos personales de terceros, identificaciones, cuentas, firmas o material sujeto a NDA.")

elif section == "Match de vacante":
    st.header("Match de vacante")
    st.write("Pega la descripción de una vacante. El análisis es por coincidencia de lenguaje y experiencia documentada; sirve para decidir qué versión del perfil conviene presentar.")
    vacancy = st.text_area("Descripción de la vacante", height=280, placeholder="Pega aquí responsabilidades, requisitos y herramientas...")
    if vacancy.strip():
        vtok = tokenize(vacancy)
        scores = []
        for tr in tracks:
            ttok = tokenize(track_text(data, tr))
            common = vtok & ttok
            score = round(100 * len(common) / max(1, len(vtok)))
            scores.append((tr, score, sorted(common)))
        scores.sort(key=lambda x: x[1], reverse=True)
        best = scores[0]
        st.subheader("Coincidencia por enfoque")
        for tr, score, common in scores:
            st.progress(min(score,100)/100, text=f"{tr}: {score}% de coincidencia textual")
        st.subheader(f"Contenido que conviene priorizar: {best[0]}")
        matched_terms = best[2][:30]
        st.write("**Términos coincidentes:** " + (", ".join(matched_terms) if matched_terms else "sin coincidencias suficientes"))
        st.caption("Este porcentaje no mide elegibilidad ni probabilidad de contratación; sólo similitud textual contra tu experiencia documentada.")
        rel_exp = [e for e in data["experience"] if best[0] in e.get("tracks", [])][:3]
        for e in rel_exp:
            with st.expander(f"{e['role']} · {e['company']}"):
                for b in e["bullets"]:
                    st.write("• " + b)

elif section == "CV ATS":
    st.header(f"CV ATS · {track}")
    ats = build_ats(data, track)
    st.text_area("Vista previa", ats, height=610)
    st.download_button("Descargar CV ATS (.txt)", ats.encode("utf-8"), file_name=f"Abraham_Yanez_{track.replace(' ','_').replace('/','-')}_ATS.txt", mime="text/plain", use_container_width=True)
    st.caption("Después lo convertiremos también a PDF/DOCX de 1–2 páginas, manteniendo esta versión limpia para sistemas ATS.")

elif section == "Admin":
    st.header("Panel de administración")
    st.write("Esta sección permite mantener el contenido separado del código. En la versión publicada se protegerá con contraseña y posteriormente puede conectarse a Google Sheets/Drive.")
    tab1, tab2, tab3 = st.tabs(["Datos generales", "Agregar evidencia", "JSON maestro"])
    with tab1:
        st.text_input("Nombre", value=p["name"], disabled=True)
        st.text_input("LinkedIn", value=p["linkedin"], disabled=True)
        st.text_input("Ubicación", value=p["location"], disabled=True)
        st.info("En este MVP los datos validados se mantienen en profile_data.json para evitar cambios accidentales. El siguiente paso es habilitar formularios persistentes.")
    with tab2:
        etype = st.selectbox("Tipo", ["Foto de proyecto", "Certificación", "Carta / reconocimiento", "Video", "Dashboard / captura", "Otro"])
        title = st.text_input("Título de evidencia")
        note = st.text_area("Descripción pública / notas de sanitización")
        uploaded = st.file_uploader("Archivo", type=["png","jpg","jpeg","pdf","mp4"])
        if uploaded and title:
            st.success("Archivo listo para clasificación. En despliegue público se guardará fuera del repositorio y se registrará sólo su referencia.")
    with tab3:
        raw = json.dumps(data, ensure_ascii=False, indent=2)
        edited = st.text_area("profile_data.json", raw, height=540)
        try:
            parsed = json.loads(edited)
            st.success("JSON válido")
            st.download_button("Descargar JSON actualizado", json.dumps(parsed, ensure_ascii=False, indent=2).encode("utf-8"), file_name="profile_data.json", mime="application/json", use_container_width=True)
        except json.JSONDecodeError as ex:
            st.error(f"JSON inválido: {ex}")

st.divider()
st.caption(f"Abraham Yañez Professional Hub · {datetime.now().year} · Perfil profesional sujeto a validación documental antes de publicación")
