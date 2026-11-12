import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from storage import PortfolioStore
from i18n import ui
from career_utils import load_career_history

BASE = Path(__file__).parent
store = PortfolioStore()

st.set_page_config(
    page_title="Abraham Yañez | Professional Hub",
    page_icon="AY",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container{max-width:1240px;padding-top:1.2rem;padding-bottom:4rem}
[data-testid="stSidebar"]{border-right:1px solid rgba(128,128,128,.16)}
.hero{padding:2.2rem 2.35rem;border:1px solid rgba(128,128,128,.22);border-radius:26px;margin-bottom:1rem;background:linear-gradient(135deg,rgba(30,55,88,.10),rgba(128,128,128,.02))}
.hero h1{font-size:2.8rem;line-height:1.03;margin:.15rem 0 .45rem;letter-spacing:-.04em}.hero p{font-size:1.03rem;line-height:1.7;max-width:930px}
.kicker{font-size:.77rem;letter-spacing:.11em;text-transform:uppercase;opacity:.62;font-weight:700}.muted{opacity:.72}.small{font-size:.9rem}.tiny{font-size:.79rem}
.pill{display:inline-block;border:1px solid rgba(128,128,128,.32);border-radius:999px;padding:.3rem .72rem;margin:.15rem .18rem .15rem 0;font-size:.84rem}
.card,.case,.stat{border:1px solid rgba(128,128,128,.22);border-radius:20px;padding:1.05rem 1.15rem;margin-bottom:.85rem}.case{height:100%}.card-title{font-size:1.08rem;font-weight:750;margin-bottom:.18rem}.stat{min-height:105px}.stat .v{font-size:1.13rem;font-weight:750;margin-top:.35rem}
.timeline{border-left:2px solid rgba(128,128,128,.22);padding-left:1.1rem;margin-left:.35rem}.timeline-item{margin:0 0 1.35rem;position:relative}.timeline-item:before{content:"";width:10px;height:10px;border-radius:50%;background:currentColor;position:absolute;left:-1.48rem;top:.42rem;opacity:.55}
/* Cleaner public presentation */
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
[data-testid="stToolbar"]{visibility:hidden;height:0;}
[data-testid="stDecoration"]{display:none;}
header[data-testid="stHeader"]{background:transparent;}

/* V5 recruiter experience */
.block-container{max-width:1320px;padding-top:1.5rem}
.hero{background:linear-gradient(125deg,#122e49,#285676);color:#fff;border:0;border-radius:24px;padding:2.5rem;box-shadow:0 16px 36px rgba(12,37,58,.12)}
.hero .muted,.hero .small{opacity:.9}
.hero h1{font-size:clamp(2rem,4vw,3.15rem);line-height:1.1}
.hero .pill{background:rgba(255,255,255,.10);border-color:rgba(255,255,255,.25)}
.card,.case,.stat{border-radius:16px;box-shadow:0 4px 20px rgba(12,37,58,.05)}
.stat{border-top:3px solid #c7a052}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:10px;min-height:42px;font-weight:600}
.stButton>button:focus-visible,.stLinkButton>a:focus-visible{outline:3px solid #c7a052;outline-offset:2px}
@media(max-width:760px){.block-container{padding:1rem .8rem 3rem}.hero{padding:1.4rem;border-radius:16px}.hero h1{font-size:2rem}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
</style>
""", unsafe_allow_html=True)


def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def refresh():
    st.rerun()


def split_lines(value):
    return [x.strip() for x in value.splitlines() if x.strip()]


def whatsapp_url(phone, message=""):
    """Build a wa.me URL from the public phone field.

    The profile currently stores a Mexican number with +52. We normalize it to
    digits only. If a 10-digit Mexican number is entered, prefix country code 52.
    """
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        digits = "52" + digits
    if not digits:
        return ""
    base = f"https://wa.me/{digits}"
    return base + (f"?text={quote(message)}" if message else "")


def build_ats(data, track, lang="es"):
    p = data["personal"]
    selected_exp = [e for e in data.get("experience", []) if track in e.get("tracks", [])]
    for item in load_career_history():
        if not any(e.get("company", "").lower() == item["company"].lower() for e in selected_exp):
            selected_exp.append({"role": item["role"], "company": item["company"], "period": item["period"], "location": "México", "bullets": [item["summary"]]})
    selected_projects = [x for x in data.get("projects", []) if track in x.get("tracks", [])]
    keys = data.get("profile_tracks", {}).get(track, {}).get("keywords", [])
    labels = ({"summary":"PROFESSIONAL SUMMARY","skills":"CORE SKILLS","exp":"EXPERIENCE","proj":"SELECTED PROJECTS","edu":"EDUCATION","tools":"TOOLS & METHODS"}
              if lang == "en" else
              {"summary":"RESUMEN PROFESIONAL","skills":"COMPETENCIAS CLAVE","exp":"EXPERIENCIA","proj":"PROYECTOS SELECCIONADOS","edu":"FORMACIÓN","tools":"HERRAMIENTAS Y MÉTODOS"})
    out = [p.get("name", "").upper(), track.upper(), f"{p.get('location','')} | {p.get('email','')} | {p.get('phone','')} | {p.get('linkedin','')}", "", labels["summary"], p.get("summary", ""), "", labels["skills"], " | ".join(keys), "", labels["exp"]]
    for e in selected_exp:
        out += [f"{e.get('role','')} | {e.get('company','')} | {e.get('period','')} | {e.get('location','')}"]
        out += ["- " + x for x in e.get("bullets", [])] + [""]
    out += [labels["proj"]]
    for pr in selected_projects[:6]:
        out.append(f"- {pr.get('title','')} | {pr.get('role','')} | {pr.get('summary','')}")
    out += ["", labels["edu"]]
    for ed in data.get("education", []):
        inst = f" | {ed.get('institution','')}" if ed.get("institution") else ""
        out.append(f"- {ed.get('degree','')}{inst}")
    out += ["", labels["tools"]]
    flat = []
    for vals in data.get("skills", {}).values(): flat += vals
    out.append(" | ".join(dict.fromkeys(flat)))
    return "\n".join(out)


def tokenize(text):
    return set(re.findall(r"[a-záéíóúñ0-9\+\#\.]{3,}", text.lower()))


def track_text(data, track):
    chunks = []
    td = data.get("profile_tracks", {}).get(track, {})
    chunks += [td.get("tagline", ""), " ".join(td.get("keywords", []))]
    for e in data.get("experience", []):
        if track in e.get("tracks", []): chunks += [e.get("role", ""), e.get("company", ""), " ".join(e.get("bullets", []))]
    for e in load_career_history():
        chunks += [e["role"], e["company"], e["summary"]]
    for p in data.get("projects", []):
        if track in p.get("tracks", []): chunks += [p.get("title", ""), p.get("sector", ""), p.get("summary", "")]
    for values in data.get("skills", {}).values(): chunks.append(" ".join(values))
    return " ".join(chunks)


def media_render(ev):
    url = ev.get("url", "")
    if not url: return
    kind = ev.get("type", "").lower()
    ext = url.lower().split("?")[0]
    try:
        if kind == "video" or ext.endswith((".mp4", ".mov", ".webm")):
            st.video(url)
        elif ext.endswith((".png", ".jpg", ".jpeg", ".webp")):
            st.image(url, use_container_width=True)
        else:
            st.link_button("Abrir / Open", url, use_container_width=True)
    except Exception:
        st.link_button("Abrir / Open", url, use_container_width=True)


# ---------------- PUBLIC PORTFOLIO (NO ADMIN OR VOICE ROUTES) ----------------
lang_choice = st.sidebar.radio("Language / Idioma", ["Español", "English"], horizontal=True)
lang = "en" if lang_choice == "English" else "es"
data = store.load(lang)
if not data:
    data = store.load("es")
p = data.get("personal", {})
pub = data.get("public_settings", {})
tracks = list(data.get("profile_tracks", {}).keys()) or ["Project Manager"]
default_track = pub.get("default_track", tracks[0])
if default_track not in tracks:
    default_track = tracks[0]

public_title = pub.get("public_title") or ("Industrial Project & Operations Leader" if lang == "en" else "Líder de Proyectos Industriales y Operaciones")
public_subtitle = pub.get("public_subtitle") or (
    "Project Management · Operations · Production · PMO · Industrial Engineering · Supply Chain"
)
default_areas_es = [
    "Dirección de proyectos y PMO",
    "Operaciones y producción",
    "Ingeniería y mejora continua",
    "Supply Chain y transformación digital",
]
default_areas_en = [
    "Project Management & PMO",
    "Operations & Production",
    "Industrial Engineering & Continuous Improvement",
    "Supply Chain & Digital Transformation",
]
value_areas = pub.get("value_areas") or (default_areas_en if lang == "en" else default_areas_es)

public_exp = [e for e in data.get("experience", []) if e.get("published", True)]
for historical in load_career_history():
    if not any(e.get("company", "").casefold() == historical["company"].casefold() for e in public_exp):
        public_exp.append({"company": historical["company"], "role": historical["role"], "period": historical["period"] + " (fechas aproximadas)", "location": "México", "bullets": [historical["summary"]], "published": True})
public_projects = [x for x in data.get("projects", []) if x.get("published", True)]
featured_exp = [e for e in public_exp if e.get("featured", False)] or public_exp[:3]
featured_projects = [x for x in public_projects if x.get("featured", False)] or public_projects[:3]

with st.sidebar:
    st.markdown("### Abraham Yañez")
    st.caption(ui(lang,"portfolio"))
    st.markdown(f"**{public_title}**")
    st.divider()
    nav = [("Inicio","home"),("Trayectoria","career"),("Casos de proyecto","projects"),("Competencias","skills"),("Formación","education")]
    if pub.get("show_evidence", True):
        nav.append(("Evidencias","evidence"))
    nav.append(("Comparar vacante","jobmatch"))
    display=[ui(lang,key) for _,key in nav]
    chosen = st.radio("Navegación", display, label_visibility="collapsed")
    section = nav[display.index(chosen)][0]
    st.divider()
    if pub.get("show_contact", True) and p.get("linkedin"):
        st.link_button("LinkedIn", p["linkedin"], use_container_width=True)
    wa_msg = pub.get("whatsapp_message_en" if lang == "en" else "whatsapp_message_es", "")
    wa_link = whatsapp_url(p.get("phone", ""), wa_msg)
    if pub.get("show_whatsapp", True) and wa_link:
        st.link_button("💬 WhatsApp", wa_link, use_container_width=True)
    st.caption(ui(lang,"visitor_note"))

if section == "Inicio":
    left,right=st.columns([3.3,1],gap="large")
    with left:
        area_html = ''.join(f'<span class="pill">{a}</span>' for a in value_areas)
        st.markdown(
            f"<div class='hero'><div class='kicker'>Professional Portfolio</div><h1>{p.get('name','')}</h1>"
            f"<div class='muted'><b>{public_title}</b></div><p>{p.get('summary','')}</p>"
            f"<div class='small muted'>{public_subtitle}</div><br><div>{area_html}</div></div>",
            unsafe_allow_html=True,
        )
        if pub.get("show_contact", True):
            b1,b2,b3=st.columns(3)
            if p.get("linkedin"):
                b1.link_button(ui(lang,"linkedin"),p["linkedin"],use_container_width=True)
            b2.download_button(
                ui(lang,"download"),
                build_ats(data,default_track,lang).encode("utf-8"),
                file_name=f"Abraham_Yanez_{default_track.replace(' ','_').replace('/','-')}_{lang}.txt",
                use_container_width=True,
            )
            wa_msg = pub.get("whatsapp_message_en" if lang == "en" else "whatsapp_message_es", "")
            wa_link = whatsapp_url(p.get("phone", ""), wa_msg)
            if pub.get("show_whatsapp", True) and wa_link:
                b3.link_button("💬 WhatsApp", wa_link, use_container_width=True)
            else:
                b3.button(ui(lang,"availability"),use_container_width=True,disabled=True)
    with right:
        if p.get("photo"):
            try:
                st.image(p["photo"],use_container_width=True)
            except Exception:
                pass
        else:
            st.markdown("<div class='card' style='text-align:center;padding:2.2rem .8rem'><div style='font-size:3.2rem;font-weight:800'>AY</div></div>",unsafe_allow_html=True)
        st.markdown(f"**{p.get('location','')}**")
        st.caption(p.get("mobility",""))

    if pub.get("show_highlights", True) and data.get("highlights"):
        cols=st.columns(max(1,min(4,len(data.get("highlights",[])))))
        for col,item in zip(cols,data.get("highlights",[])[:4]):
            col.markdown(f"<div class='stat'><div class='kicker'>{item.get('label','')}</div><div class='v'>{item.get('value','')}</div></div>",unsafe_allow_html=True)

    st.markdown("### " + ("¿Qué perfil necesitas?" if lang == "es" else "Which profile are you hiring for?"))
    selected_track = st.selectbox("Perfil profesional" if lang == "es" else "Professional track", tracks, index=tracks.index(default_track) if default_track in tracks else 0, key="recruiter_track")
    track_info = data.get("profile_tracks", {}).get(selected_track, {})
    st.info(track_info.get("tagline", ""))
    st.download_button("Descargar CV orientado a este puesto" if lang == "es" else "Download role-focused resume", build_ats(data, selected_track, lang).encode("utf-8"), file_name="Abraham_Yanez_" + selected_track.replace(" ", "_").replace("/", "-") + "_" + lang + ".txt", mime="text/plain", key="recruiter_cv_download")

    st.markdown("### " + ("Áreas donde aporto valor" if lang == "es" else "Where I add value"))
    area_cols = st.columns(2)
    for i, area in enumerate(value_areas[:4]):
        area_cols[i % 2].markdown(f"<div class='card'><div class='card-title'>{area}</div></div>", unsafe_allow_html=True)

    if featured_exp:
        st.markdown("### " + ("Experiencia destacada" if lang == "es" else "Featured experience"))
        cols=st.columns(max(1,min(3,len(featured_exp[:3]))))
        for col,e in zip(cols,featured_exp[:3]):
            col.markdown(
                f"<div class='case'><div class='kicker'>{e.get('period','')}</div><div class='card-title'>{e.get('role','')}</div>"
                f"<div class='muted small'>{e.get('company','')}</div><br><div class='small'>{(e.get('bullets') or [''])[0]}</div></div>",
                unsafe_allow_html=True,
            )

    if featured_projects:
        st.markdown("### " + ("Proyectos seleccionados" if lang == "es" else "Selected projects"))
        cols=st.columns(max(1,min(3,len(featured_projects[:3]))))
        for col,pr in zip(cols,featured_projects[:3]):
            col.markdown(
                f"<div class='case'><div class='kicker'>{pr.get('sector','')} · {pr.get('region','')}</div>"
                f"<div class='card-title'>{pr.get('title','')}</div><div class='small'>{pr.get('summary','')}</div></div>",
                unsafe_allow_html=True,
            )

elif section == "Trayectoria":
    st.header(ui(lang,"career"))
    st.caption("Experiencia seleccionada para la vista pública." if lang == "es" else "Experience selected for the public portfolio.")
    st.caption("Las fechas de 2007 a 2018 son aproximadas y están pendientes de confirmación." if lang == "es" else "Dates between 2007 and 2018 are approximate and pending confirmation.")
    concise = st.toggle("Vista ejecutiva resumida" if lang == "es" else "Concise executive view", value=True, key="career_concise")
    st.markdown("<div class='timeline'>",unsafe_allow_html=True)
    for e in public_exp:
        st.markdown("<div class='timeline-item'>",unsafe_allow_html=True)
        st.subheader(f"{e.get('role','')} · {e.get('company','')}")
        st.caption(f"{e.get('period','')} · {e.get('location','')}")
        for b in (e.get("bullets",[])[:2] if concise else e.get("bullets",[])):
            st.write("• "+b)
        st.markdown("</div>",unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

elif section == "Casos de proyecto":
    st.header(ui(lang,"projects"))
    for i in range(0,len(public_projects),2):
        cols=st.columns(2)
        for col,pr in zip(cols,public_projects[i:i+2]):
            with col:
                st.markdown(
                    f"<div class='case'><div class='kicker'>{pr.get('sector','')} · {pr.get('region','')}</div>"
                    f"<div class='card-title'>{pr.get('title','')}</div><div class='small'><b>{ui(lang,'role')}:</b> {pr.get('role','')} "
                    f"&nbsp; <b>{ui(lang,'status')}:</b> {pr.get('status','')}</div><br><div>{pr.get('summary','')}</div>"
                    f"<br><div class='muted tiny'>{pr.get('evidence_note','')}</div></div>",
                    unsafe_allow_html=True,
                )

elif section == "Comparar vacante":
    st.header(ui(lang,"jobmatch"))
    description = st.text_area(ui(lang,"paste_job"), height=220)
    if st.button(ui(lang,"analyze")):
        job_terms = tokenize(description)
        profile_terms = tokenize(track_text(data, default_track))
        if not job_terms:
            st.info("Pega una descripción de vacante para analizarla." if lang == "es" else "Paste a job description to analyze.")
        else:
            common = sorted(job_terms & profile_terms)
            missing = sorted(job_terms - profile_terms)
            st.metric("Coincidencia de términos" if lang == "es" else "Keyword overlap", f"{len(common)/len(job_terms):.0%}")
            st.write("**Coincidencias / Matches:**", ", ".join(common[:40]) or "—")
            st.write("**Por revisar / Not found:**", ", ".join(missing[:40]) or "—")
            st.caption(ui(lang,"match_note"))

elif section == "Competencias":
    st.header(ui(lang,"skills"))
    for area,skills in data.get("skills",{}).items():
        st.markdown(f"### {area}")
        st.markdown(" ".join(f"`{s}`" for s in skills))

elif section == "Formación":
    st.header(ui(lang,"credentials"))
    for e in data.get("education",[]):
        st.markdown(f"### {e.get('degree','')}")
        st.write(e.get("institution","") or ("Institution pending" if lang=="en" else "Institución pendiente"))
        st.caption(e.get("credential",""))
    if data.get("certifications"):
        st.divider()
        st.subheader("Certifications" if lang=="en" else "Certificaciones / membresías")
        for c in data.get("certifications",[]):
            st.markdown(f"**{c.get('name','')}** — {c.get('status','')}")

elif section == "Evidencias":
    st.header(ui(lang,"evidence"))
    evs=[e for e in data.get("evidence",[]) if e.get("published",True)]
    if not evs:
        st.info(ui(lang,"no_evidence"))
    for i in range(0,len(evs),3):
        cols=st.columns(3)
        for col,ev in zip(cols,evs[i:i+3]):
            with col:
                st.markdown(
                    f"<div class='card'><div class='kicker'>{ev.get('type','')}</div><div class='card-title'>{ev.get('title','')}</div>"
                    f"<div class='small'>{ev.get('description','')}</div><div class='muted tiny'>{ev.get('related','')}</div></div>",
                    unsafe_allow_html=True,
                )
                media_render(ev)

# ---------------- DIRECT CONTACT CTA ----------------
wa_msg = pub.get("whatsapp_message_en" if lang == "en" else "whatsapp_message_es", "")
wa_link = whatsapp_url(p.get("phone", ""), wa_msg)
if pub.get("show_whatsapp", True) and wa_link:
    st.divider()
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("### " + ("¿Quieres conversar directamente?" if lang == "es" else "Would you like to talk directly?"))
        st.caption(
            "Abre una conversación conmigo por WhatsApp para coordinar una entrevista o comentar una oportunidad."
            if lang == "es" else
            "Open a WhatsApp conversation with me to coordinate an interview or discuss an opportunity."
        )
    with c2:
        st.write("")
        st.link_button("💬 " + ("Contactar por WhatsApp" if lang == "es" else "Contact via WhatsApp"), wa_link, use_container_width=True)

# ---------------- RECRUITER DECISION CTA ----------------
if pub.get("show_recruiter_decision", True):
    st.divider()
    st.markdown("### " + ("¿Deseas continuar con mi candidatura?" if lang == "es" else "Would you like to continue with my application?"))
    st.caption(
        "Esta respuesta es privada y me permite dar seguimiento correcto al proceso de selección."
        if lang == "es" else
        "Your response is private and helps me follow up appropriately on the recruitment process."
    )

    if "recruiter_decision" not in st.session_state:
        st.session_state.recruiter_decision = None

    cta_a, cta_b = st.columns(2)
    continue_label = "✅ Sí, continuar con el proceso" if lang == "es" else "✅ Yes, continue the process"
    decline_label = "⛔ Cerrar / declinar candidatura" if lang == "es" else "⛔ Close / decline application"
    if cta_a.button(continue_label, use_container_width=True, type="primary", key="recruiter_continue"):
        st.session_state.recruiter_decision = "continue"
        st.session_state.recruiter_feedback_sent = False
    if cta_b.button(decline_label, use_container_width=True, key="recruiter_decline"):
        st.session_state.recruiter_decision = "decline"
        st.session_state.recruiter_feedback_sent = False

    if st.session_state.recruiter_decision:
        decision = st.session_state.recruiter_decision
        positive = decision == "continue"
        st.info(
            ("Gracias. Completa estos datos para que pueda dar seguimiento al siguiente paso." if positive else
             "Gracias por cerrar el ciclo. Tu respuesta evita seguimientos innecesarios y me ayuda a gestionar otras oportunidades.")
            if lang == "es" else
            ("Thank you. Please complete these details so I can follow up on the next step." if positive else
             "Thank you for closing the loop. Your response prevents unnecessary follow-ups and helps me manage other opportunities.")
        )
        with st.form("recruiter_feedback_form", clear_on_submit=False):
            recruiter_name = st.text_input("Nombre del reclutador" if lang == "es" else "Recruiter name")
            company = st.text_input("Empresa" if lang == "es" else "Company")
            role_title = st.text_input("Vacante / posición" if lang == "es" else "Role / position")
            email = st.text_input("Correo de contacto (opcional)" if lang == "es" else "Contact email (optional)")
            message = st.text_area("Comentario / siguiente paso (opcional)" if lang == "es" else "Comment / next step (optional)", height=110)
            consent = st.checkbox(
                "Confirmo que deseo enviar esta respuesta al candidato."
                if lang == "es" else
                "I confirm that I want to send this response to the candidate."
            )
            submitted = st.form_submit_button(
                "Enviar decisión" if lang == "es" else "Send decision",
                use_container_width=True,
                type="primary",
            )
        if submitted:
            if not consent:
                st.error("Confirma el envío de la respuesta." if lang == "es" else "Please confirm that you want to send the response.")
            elif not company.strip() and not recruiter_name.strip():
                st.error("Indica al menos tu nombre o empresa." if lang == "es" else "Please provide at least your name or company.")
            elif st.session_state.get("recruiter_feedback_sent"):
                st.warning("Esta respuesta ya fue enviada en esta sesión." if lang == "es" else "This response has already been sent in this session.")
            else:
                payload = {
                    "decision": decision,
                    "recruiter_name": recruiter_name.strip(),
                    "company": company.strip(),
                    "email": email.strip(),
                    "role_title": role_title.strip(),
                    "message": message.strip(),
                    "language": lang,
                }
                ok = store.save_recruiter_feedback(payload)
                if ok:
                    store.notify_recruiter_feedback(payload)
                    st.session_state.recruiter_feedback_sent = True
                    st.session_state.recruiter_decision = None
                    if positive:
                        st.success("Respuesta registrada. Gracias por continuar con el proceso." if lang == "es" else "Response recorded. Thank you for continuing the process.")
                    else:
                        st.success("Candidatura cerrada correctamente. Gracias por informar la decisión." if lang == "es" else "Application closed successfully. Thank you for sharing the decision.")
                else:
                    st.error(("No fue posible registrar la respuesta. " if lang == "es" else "The response could not be recorded. ") + (store.last_error or ""))

st.divider()
st.caption(f"Abraham Yañez Professional Hub · {datetime.now().year}")
