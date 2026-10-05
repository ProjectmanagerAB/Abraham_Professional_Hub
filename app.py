import copy
import hashlib
import hmac
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from storage import PortfolioStore
from i18n import ui, translate_profile

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
.adminbar{padding:.75rem 1rem;border:1px solid rgba(128,128,128,.25);border-radius:16px;margin-bottom:1rem;background:rgba(128,128,128,.06)}
/* Cleaner public presentation */
#MainMenu{visibility:hidden;}
footer{visibility:hidden;}
[data-testid="stToolbar"]{visibility:hidden;height:0;}
[data-testid="stDecoration"]{display:none;}
header[data-testid="stHeader"]{background:transparent;}
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


def is_admin_route():
    try:
        return st.query_params.get("admin") == "1"
    except Exception:
        return False


def admin_authenticated():
    return st.session_state.get("admin_authenticated", False)


def check_password(password):
    expected = get_secret("ADMIN_PASSWORD", "")
    if not expected:
        return False
    return hmac.compare_digest(hashlib.sha256(password.encode()).digest(), hashlib.sha256(expected.encode()).digest())


def save_admin(data, lang="es"):
    ok = store.save(data, lang)
    if ok:
        if lang == "es":
            st.session_state.admin_data = copy.deepcopy(data)
        st.success("Cambios guardados correctamente en Supabase." if store.remote else "Cambios guardados correctamente en el almacenamiento local.")
        return True
    detail = getattr(store, "last_error", None) or "No se recibió confirmación del almacenamiento."
    st.error("No se pudieron guardar los cambios. " + detail)
    return False


# ---------------- PUBLIC / ADMIN ROUTING ----------------
if is_admin_route():
    if not admin_authenticated():
        st.title("Administrador · Abraham Professional Hub")
        st.caption("Acceso privado. La contraseña se configura en Streamlit Secrets y no se almacena en GitHub.")
        if not get_secret("ADMIN_PASSWORD", ""):
            st.error("Falta configurar ADMIN_PASSWORD en Streamlit Secrets.")
        with st.form("login"):
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
        if submitted:
            if check_password(password):
                st.session_state.admin_authenticated = True
                st.session_state.admin_data = copy.deepcopy(store.load("es"))
                refresh()
            else:
                st.error("Contraseña incorrecta.")
        st.stop()

    if "admin_data" not in st.session_state:
        st.session_state.admin_data = copy.deepcopy(store.load("es"))
    data = st.session_state.admin_data
    tracks = list(data.get("profile_tracks", {}).keys())

    st.markdown(f"<div class='adminbar'><b>Modo administrador</b> · almacenamiento: {store.mode} · edición de la versión maestra en español.</div>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns([1,1,1,2])
    if c1.button("Guardar todo", use_container_width=True): save_admin(data)
    if c2.button("Recargar", use_container_width=True):
        st.session_state.admin_data = copy.deepcopy(store.load("es")); refresh()
    if c3.button("Cerrar sesión", use_container_width=True):
        st.session_state.admin_authenticated = False; refresh()
    c4.link_button("Abrir vista pública", "?", use_container_width=True)

    section = st.sidebar.radio("Administración", ["Panel", "Publicación", "Perfil", "Perfiles internos CV/ATS", "Experiencia", "Proyectos", "Competencias", "Formación", "Certificaciones", "Evidencias", "Decisiones RH", "Traducción EN", "Avanzado"])

    if section == "Panel":
        st.header("Panel de administración")
        st.write("Edita el portafolio desde aquí. Los reclutadores sólo ven la vista pública y nunca estos controles.")
        a,b,c,d = st.columns(4)
        a.metric("Experiencias", len(data.get("experience", [])))
        b.metric("Proyectos", len(data.get("projects", [])))
        c.metric("Evidencias", len(data.get("evidence", [])))
        d.metric("Modo de datos", store.mode)
        if store.mode == "Local JSON":
            st.warning("La app funciona, pero en Streamlit Cloud los cambios locales pueden perderse al reiniciar. Configura Supabase para edición persistente.")
        st.info("Acceso administrador: agrega ?admin=1 al final de la URL pública. Ejemplo: https://tuapp.streamlit.app/?admin=1")

    elif section == "Publicación":
        st.header("Configuración de la vista pública")
        st.caption("Estos controles definen qué verá un reclutador. Los perfiles internos CV/ATS no se muestran públicamente.")
        pub = data.setdefault("public_settings", {})
        default_areas = [
            "Project Management & PMO",
            "Operations & Production",
            "Industrial Engineering & Continuous Improvement",
            "Supply Chain & Digital Transformation",
        ]
        with st.form("publication_form"):
            pub["public_title"] = st.text_input("Título principal público", pub.get("public_title", "Industrial Project & Operations Leader"))
            pub["public_subtitle"] = st.text_area(
                "Mensaje corto de posicionamiento",
                pub.get("public_subtitle", "Project Management · Operations · Production · PMO · Industrial Engineering · Supply Chain"),
                height=90,
            )
            pub["value_areas"] = split_lines(st.text_area(
                "Áreas donde aporto valor (una por línea)",
                "\n".join(pub.get("value_areas", default_areas)),
                height=130,
            ))
            available_tracks = list(data.get("profile_tracks", {}).keys()) or ["Project Manager"]
            current_track = pub.get("default_track", available_tracks[0])
            default_idx = available_tracks.index(current_track) if current_track in available_tracks else 0
            pub["default_track"] = st.selectbox("Perfil interno usado para el CV ATS descargable", available_tracks, index=default_idx)
            pub["show_highlights"] = st.checkbox("Mostrar indicadores de portada", pub.get("show_highlights", True))
            pub["show_evidence"] = st.checkbox("Mostrar sección Evidencias", pub.get("show_evidence", True))
            pub["show_recruiter_decision"] = st.checkbox("Mostrar decisión del reclutador", pub.get("show_recruiter_decision", True))
            pub["show_contact"] = st.checkbox("Mostrar botones LinkedIn / CV", pub.get("show_contact", True))
            pub["show_whatsapp"] = st.checkbox("Mostrar botón de WhatsApp", pub.get("show_whatsapp", True))
            pub["whatsapp_message_es"] = st.text_area(
                "Mensaje precargado de WhatsApp · Español",
                pub.get("whatsapp_message_es", "Hola Abraham, revisé tu portafolio profesional y me gustaría conversar contigo sobre una oportunidad laboral."),
                height=90,
            )
            pub["whatsapp_message_en"] = st.text_area(
                "Mensaje precargado de WhatsApp · English",
                pub.get("whatsapp_message_en", "Hello Abraham, I reviewed your professional portfolio and I would like to speak with you about a career opportunity."),
                height=90,
            )
            save = st.form_submit_button("Guardar configuración pública", use_container_width=True)
        if save:
            save_admin(data); refresh()
        st.info("Recomendación: mantén una sola identidad pública. Usa los perfiles internos sólo para adaptar CVs y postulaciones.")

    elif section == "Perfil":
        st.header("Perfil general")
        p = data.setdefault("personal", {})
        with st.form("profile_form"):
            p["name"] = st.text_input("Nombre", p.get("name", ""))
            p["headline"] = st.text_input("Titular profesional", p.get("headline", ""))
            p["summary"] = st.text_area("Resumen profesional", p.get("summary", ""), height=170)
            p["location"] = st.text_input("Ubicación", p.get("location", ""))
            p["mobility"] = st.text_input("Disponibilidad / movilidad", p.get("mobility", ""))
            p["email"] = st.text_input("Correo", p.get("email", ""))
            p["phone"] = st.text_input("Teléfono", p.get("phone", ""))
            p["linkedin"] = st.text_input("LinkedIn", p.get("linkedin", ""))
            save = st.form_submit_button("Guardar perfil", use_container_width=True)
        if save: save_admin(data)
        st.subheader("Fotografía profesional")
        photo = st.file_uploader("Subir o reemplazar foto", type=["png","jpg","jpeg","webp"], key="profile_photo")
        if photo and st.button("Guardar fotografía"):
            p["photo"] = store.upload_media(photo, "profile")
            save_admin(data); refresh()
        if p.get("photo"): st.image(p["photo"], width=220)
        st.subheader("Indicadores de portada")
        highlights = data.setdefault("highlights", [])
        edited_highlights = st.data_editor(highlights, num_rows="dynamic", use_container_width=True, key="highlights_editor")
        if st.button("Guardar indicadores", use_container_width=True):
            try:
                data["highlights"] = edited_highlights.to_dict("records")
            except Exception:
                data["highlights"] = edited_highlights
            save_admin(data); refresh()

    elif section == "Perfiles internos CV/ATS":
        st.header("Perfiles internos para CV / ATS")
        st.caption("No se muestran en la vista pública. Sirven para adaptar CVs y candidaturas a distintas vacantes.")
        pt = data.setdefault("profile_tracks", {})
        names = list(pt.keys())
        selected = st.selectbox("Editar enfoque", ["+ Nuevo enfoque"] + names)
        new = selected == "+ Nuevo enfoque"
        current = {"tagline":"","keywords":[]} if new else pt[selected]
        with st.form("track_form"):
            name = st.text_input("Nombre del enfoque", "" if new else selected)
            tagline = st.text_area("Descripción", current.get("tagline", ""))
            keywords = st.text_area("Palabras clave (una por línea)", "\n".join(current.get("keywords", [])))
            save = st.form_submit_button("Guardar enfoque", use_container_width=True)
        if save and name.strip():
            if not new and name != selected: pt.pop(selected, None)
            pt[name.strip()] = {"tagline":tagline.strip(), "keywords":split_lines(keywords)}
            save_admin(data); refresh()
        if not new and st.button("Eliminar enfoque", type="secondary"):
            pt.pop(selected, None); save_admin(data); refresh()

    elif section == "Experiencia":
        st.header("Experiencia profesional")
        items = data.setdefault("experience", [])
        labels = [f"{i+1}. {x.get('role','')} · {x.get('company','')}" for i,x in enumerate(items)]
        selected = st.selectbox("Registro", ["+ Nueva experiencia"] + labels)
        new = selected == "+ Nueva experiencia"
        idx = None if new else labels.index(selected)
        cur = {"role":"","company":"","location":"","period":"","tracks":[],"bullets":[],"published":True,"featured":False} if new else items[idx]
        with st.form("exp_form"):
            role = st.text_input("Puesto", cur.get("role", "")); company = st.text_input("Empresa / organización", cur.get("company", ""))
            location = st.text_input("Ubicación", cur.get("location", "")); period = st.text_input("Periodo", cur.get("period", ""))
            selected_tracks = st.multiselect("Perfiles internos CV/ATS", tracks, default=[x for x in cur.get("tracks", []) if x in tracks])
            published = st.checkbox("Visible en el portafolio público", cur.get("published", True))
            featured = st.checkbox("Destacar en la portada", cur.get("featured", False))
            bullets = st.text_area("Responsabilidades / logros (uno por línea)", "\n".join(cur.get("bullets", [])), height=220)
            save = st.form_submit_button("Guardar experiencia", use_container_width=True)
        record = {"role":role,"company":company,"location":location,"period":period,"tracks":selected_tracks,"bullets":split_lines(bullets),"published":published,"featured":featured}
        if save and role.strip():
            if new: items.insert(0, record)
            else: items[idx] = record
            save_admin(data); refresh()
        if not new and st.button("Eliminar experiencia"):
            items.pop(idx); save_admin(data); refresh()

    elif section == "Proyectos":
        st.header("Casos y proyectos")
        items = data.setdefault("projects", [])
        labels = [f"{i+1}. {x.get('title','')}" for i,x in enumerate(items)]
        selected = st.selectbox("Proyecto", ["+ Nuevo proyecto"] + labels)
        new = selected == "+ Nuevo proyecto"; idx = None if new else labels.index(selected)
        cur = {"title":"","sector":"","region":"","role":"","status":"","tracks":[],"summary":"","evidence_note":"","published":True,"featured":False} if new else items[idx]
        with st.form("project_form"):
            title = st.text_input("Título", cur.get("title", "")); sector = st.text_input("Sector", cur.get("sector", "")); region = st.text_input("Región", cur.get("region", ""))
            role = st.text_input("Rol", cur.get("role", "")); status = st.text_input("Estado", cur.get("status", "")); selected_tracks = st.multiselect("Perfiles internos CV/ATS", tracks, default=[x for x in cur.get("tracks", []) if x in tracks])
            published = st.checkbox("Visible en el portafolio público", cur.get("published", True))
            featured = st.checkbox("Destacar en la portada", cur.get("featured", False))
            summary = st.text_area("Descripción / caso", cur.get("summary", ""), height=180); note = st.text_area("Nota pública de evidencia / confidencialidad", cur.get("evidence_note", ""))
            save = st.form_submit_button("Guardar proyecto", use_container_width=True)
        record = {"title":title,"sector":sector,"region":region,"role":role,"status":status,"tracks":selected_tracks,"summary":summary,"evidence_note":note,"published":published,"featured":featured}
        if save and title.strip():
            if new: items.insert(0, record)
            else: items[idx] = record
            save_admin(data); refresh()
        if not new and st.button("Eliminar proyecto"):
            items.pop(idx); save_admin(data); refresh()

    elif section == "Competencias":
        st.header("Competencias")
        skills = data.setdefault("skills", {})
        areas = list(skills.keys())
        selected = st.selectbox("Área", ["+ Nueva área"] + areas)
        new = selected == "+ Nueva área"; cur = [] if new else skills[selected]
        with st.form("skills_form"):
            area = st.text_input("Nombre del área", "" if new else selected)
            values = st.text_area("Competencias (una por línea)", "\n".join(cur), height=250)
            save = st.form_submit_button("Guardar competencias", use_container_width=True)
        if save and area.strip():
            if not new and area != selected: skills.pop(selected, None)
            skills[area.strip()] = split_lines(values); save_admin(data); refresh()
        if not new and st.button("Eliminar área"):
            skills.pop(selected, None); save_admin(data); refresh()

    elif section == "Formación":
        st.header("Formación académica")
        items = data.setdefault("education", [])
        labels = [f"{i+1}. {x.get('degree','')}" for i,x in enumerate(items)]
        selected = st.selectbox("Registro", ["+ Nueva formación"] + labels)
        new = selected == "+ Nueva formación"; idx = None if new else labels.index(selected)
        cur = {"degree":"","institution":"","credential":""} if new else items[idx]
        with st.form("edu_form"):
            degree = st.text_input("Grado / programa", cur.get("degree", "")); institution = st.text_input("Institución", cur.get("institution", "")); credential = st.text_input("Cédula / dato de respaldo", cur.get("credential", ""))
            save = st.form_submit_button("Guardar formación", use_container_width=True)
        if save and degree.strip():
            rec={"degree":degree,"institution":institution,"credential":credential}
            if new: items.append(rec)
            else: items[idx]=rec
            save_admin(data); refresh()
        if not new and st.button("Eliminar formación"):
            items.pop(idx); save_admin(data); refresh()

    elif section == "Certificaciones":
        st.header("Certificaciones y membresías")
        items = data.setdefault("certifications", [])
        labels=[f"{i+1}. {x.get('name','')}" for i,x in enumerate(items)]
        selected=st.selectbox("Registro", ["+ Nueva certificación"]+labels)
        new=selected=="+ Nueva certificación"; idx=None if new else labels.index(selected); cur={"name":"","status":""} if new else items[idx]
        with st.form("cert_form"):
            name=st.text_input("Nombre",cur.get("name","")); status=st.text_area("Descripción / estado",cur.get("status","")); save=st.form_submit_button("Guardar certificación",use_container_width=True)
        if save and name.strip():
            rec={"name":name,"status":status}; items.append(rec) if new else items.__setitem__(idx,rec); save_admin(data); refresh()
        if not new and st.button("Eliminar certificación"):
            items.pop(idx); save_admin(data); refresh()

    elif section == "Evidencias":
        st.header("Evidencias multimedia")
        st.caption("Sube únicamente material público o sanitizado. Puedes asociarlo a proyectos, formación, certificaciones o experiencia.")
        items = data.setdefault("evidence", [])
        with st.expander("+ Agregar evidencia", expanded=True):
            title = st.text_input("Título", key="ev_title")
            etype = st.selectbox("Tipo", ["Imagen","Video","PDF / documento","Certificación","Carta / reconocimiento","Dashboard / captura","Otro"], key="ev_type")
            description = st.text_area("Descripción pública", key="ev_desc")
            related = st.text_input("Relacionado con (proyecto / puesto / formación)", key="ev_related")
            external = st.text_input("URL externa opcional (YouTube, Vimeo, Drive público, etc.)", key="ev_url")
            uploaded = st.file_uploader("O subir archivo", type=["png","jpg","jpeg","webp","pdf","mp4","mov","webm"], key="ev_file")
            if st.button("Publicar evidencia", use_container_width=True):
                if not title.strip(): st.error("Escribe un título.")
                elif not external.strip() and not uploaded: st.error("Agrega una URL o un archivo.")
                else:
                    url = external.strip() or store.upload_media(uploaded, "evidence")
                    items.insert(0,{"title":title.strip(),"type":etype,"description":description.strip(),"related":related.strip(),"url":url,"published":True})
                    save_admin(data); refresh()
        st.subheader("Biblioteca publicada")
        for i,ev in enumerate(items):
            with st.expander(f"{i+1}. {ev.get('title','')}"):
                ev["title"] = st.text_input("Título", ev.get("title",""), key=f"evt{i}")
                ev["description"] = st.text_area("Descripción", ev.get("description",""), key=f"evd{i}")
                ev["related"] = st.text_input("Relacionado con", ev.get("related",""), key=f"evr{i}")
                ev["url"] = st.text_input("URL / ruta", ev.get("url",""), key=f"evu{i}")
                ev["published"] = st.checkbox("Visible públicamente", ev.get("published",True), key=f"evp{i}")
                a,b=st.columns(2)
                if a.button("Guardar",key=f"evs{i}",use_container_width=True): save_admin(data); refresh()
                if b.button("Eliminar",key=f"evx{i}",use_container_width=True): items.pop(i); save_admin(data); refresh()

    elif section == "Decisiones RH":
        st.header("Decisiones de reclutadores")
        st.caption("Bandeja privada. Aquí se registran únicamente respuestas enviadas desde la vista pública.")
        rows = store.list_recruiter_feedback(200)
        if not rows:
            st.info("Todavía no hay decisiones registradas.")
        else:
            for row in rows:
                positive = row.get("decision") == "continue"
                icon = "✅" if positive else "⛔"
                label = "CONTINUAR PROCESO" if positive else "CERRAR / DECLINAR"
                title = f"{icon} {label} · {row.get('company') or 'Empresa no indicada'}"
                with st.expander(title):
                    a,b = st.columns(2)
                    a.write(f"**Reclutador:** {row.get('recruiter_name') or 'No indicado'}")
                    a.write(f"**Correo:** {row.get('email') or 'No indicado'}")
                    b.write(f"**Vacante:** {row.get('role_title') or 'No indicada'}")
                    b.write(f"**Fecha:** {row.get('created_at') or ''}")
                    if row.get("message"):
                        st.write("**Comentario:**")
                        st.write(row.get("message"))

    elif section == "Traducción EN":
        st.header("Versión en inglés")
        st.write("La vista pública en inglés usa una copia independiente. Cuando modifiques el español, genera de nuevo la traducción y después puedes revisarla desde la vista pública.")
        if st.button("Generar / actualizar versión completa en inglés", use_container_width=True):
            with st.spinner("Traduciendo contenido..."):
                translated = translate_profile(data)
                store.save(translated, "en")
            st.success("Versión en inglés actualizada.")
        st.warning("La traducción automática debe revisarse especialmente en términos técnicos, cargos y nombres propios.")

    elif section == "Avanzado":
        st.header("Editor avanzado")
        raw = st.text_area("JSON maestro", json.dumps(data,ensure_ascii=False,indent=2), height=650)
        if st.button("Validar y guardar JSON", use_container_width=True):
            try:
                parsed=json.loads(raw); st.session_state.admin_data=parsed; save_admin(parsed); refresh()
            except json.JSONDecodeError as ex: st.error(f"JSON inválido: {ex}")
        st.download_button("Descargar respaldo JSON", json.dumps(data,ensure_ascii=False,indent=2).encode("utf-8"), "profile_backup.json", "application/json", use_container_width=True)

    st.divider(); st.caption(f"Abraham Professional Hub · Admin · {datetime.now().year}")
    st.stop()

# ---------------- PUBLIC VIEW ----------------
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
    st.markdown("<div class='timeline'>",unsafe_allow_html=True)
    for e in public_exp:
        st.markdown("<div class='timeline-item'>",unsafe_allow_html=True)
        st.subheader(f"{e.get('role','')} · {e.get('company','')}")
        st.caption(f"{e.get('period','')} · {e.get('location','')}")
        for b in e.get("bullets",[]):
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
