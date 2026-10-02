import copy
import hashlib
import hmac
import json
import re
from datetime import datetime
from pathlib import Path

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
    store.save(data, lang)
    if lang == "es": st.session_state.admin_data = copy.deepcopy(data)
    st.success("Cambios guardados correctamente.")


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

    section = st.sidebar.radio("Administración", ["Panel", "Perfil", "Enfoques", "Experiencia", "Proyectos", "Competencias", "Formación", "Certificaciones", "Evidencias", "Traducción EN", "Avanzado"])

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

    elif section == "Enfoques":
        st.header("Enfoques profesionales")
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
        cur = {"role":"","company":"","location":"","period":"","tracks":[],"bullets":[]} if new else items[idx]
        with st.form("exp_form"):
            role = st.text_input("Puesto", cur.get("role", "")); company = st.text_input("Empresa / organización", cur.get("company", ""))
            location = st.text_input("Ubicación", cur.get("location", "")); period = st.text_input("Periodo", cur.get("period", ""))
            selected_tracks = st.multiselect("Mostrar en estos perfiles", tracks, default=[x for x in cur.get("tracks", []) if x in tracks])
            bullets = st.text_area("Responsabilidades / logros (uno por línea)", "\n".join(cur.get("bullets", [])), height=220)
            save = st.form_submit_button("Guardar experiencia", use_container_width=True)
        record = {"role":role,"company":company,"location":location,"period":period,"tracks":selected_tracks,"bullets":split_lines(bullets)}
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
        cur = {"title":"","sector":"","region":"","role":"","status":"","tracks":[],"summary":"","evidence_note":""} if new else items[idx]
        with st.form("project_form"):
            title = st.text_input("Título", cur.get("title", "")); sector = st.text_input("Sector", cur.get("sector", "")); region = st.text_input("Región", cur.get("region", ""))
            role = st.text_input("Rol", cur.get("role", "")); status = st.text_input("Estado", cur.get("status", "")); selected_tracks = st.multiselect("Perfiles", tracks, default=[x for x in cur.get("tracks", []) if x in tracks])
            summary = st.text_area("Descripción / caso", cur.get("summary", ""), height=180); note = st.text_area("Nota pública de evidencia / confidencialidad", cur.get("evidence_note", ""))
            save = st.form_submit_button("Guardar proyecto", use_container_width=True)
        record = {"title":title,"sector":sector,"region":region,"role":role,"status":status,"tracks":selected_tracks,"summary":summary,"evidence_note":note}
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
if not data: data = store.load("es")
p = data.get("personal", {})
tracks = list(data.get("profile_tracks", {}).keys())
if not tracks: tracks=["Project Manager"]

with st.sidebar:
    st.markdown("### Abraham Yañez")
    st.caption(ui(lang,"portfolio"))
    track = st.selectbox(ui(lang,"focus"), tracks, index=0)
    st.caption(data.get("profile_tracks", {}).get(track, {}).get("tagline", ""))
    st.divider()
    nav = [("Inicio","home"),("Trayectoria","career"),("Casos de proyecto","projects"),("Competencias","skills"),("Formación","education"),("Evidencias","evidence"),("Match de vacante","jobmatch"),("CV ATS","resume")]
    display=[ui(lang,key) for _,key in nav]
    chosen = st.radio("Navegación", display, label_visibility="collapsed")
    section = nav[display.index(chosen)][0]
    st.divider()
    if p.get("linkedin"): st.link_button("LinkedIn", p["linkedin"], use_container_width=True)
    st.caption(ui(lang,"visitor_note"))

keywords = data.get("profile_tracks", {}).get(track, {}).get("keywords", [])

if section == "Inicio":
    left,right=st.columns([3.3,1],gap="large")
    with left:
        st.markdown(f"<div class='hero'><div class='kicker'>Professional Portfolio</div><h1>{p.get('name','')}</h1><div class='muted'><b>{p.get('headline','')}</b></div><p>{p.get('summary','')}</p><div>{''.join(f'<span class="pill">{k}</span>' for k in keywords)}</div></div>", unsafe_allow_html=True)
        b1,b2,b3=st.columns(3)
        if p.get("linkedin"): b1.link_button(ui(lang,"linkedin"),p["linkedin"],use_container_width=True)
        b2.download_button(ui(lang,"download"), build_ats(data,track,lang).encode("utf-8"), file_name=f"Abraham_Yanez_{track.replace(' ','_').replace('/','-')}_{lang}.txt", use_container_width=True)
        b3.button(ui(lang,"availability"),use_container_width=True,disabled=True)
    with right:
        if p.get("photo"):
            try: st.image(p["photo"],use_container_width=True)
            except Exception: pass
        else:
            st.markdown("<div class='card' style='text-align:center;padding:2.2rem .8rem'><div style='font-size:3.2rem;font-weight:800'>AY</div></div>",unsafe_allow_html=True)
        st.markdown(f"**{p.get('location','')}**"); st.caption(p.get("mobility",""))
    st.markdown(f"### {ui(lang,'selected')}"); st.write(data.get("profile_tracks",{}).get(track,{}).get("tagline",""))
    cols=st.columns(max(1,min(4,len(data.get("highlights",[])))))
    for col,item in zip(cols,data.get("highlights",[])[:4]): col.markdown(f"<div class='stat'><div class='kicker'>{item.get('label','')}</div><div class='v'>{item.get('value','')}</div></div>",unsafe_allow_html=True)
    st.markdown(f"### {ui(lang,'demonstrate')}")
    exp=[e for e in data.get("experience",[]) if track in e.get("tracks",[])][:3]
    cols=st.columns(max(1,len(exp)))
    for col,e in zip(cols,exp): col.markdown(f"<div class='case'><div class='kicker'>{e.get('period','')}</div><div class='card-title'>{e.get('role','')}</div><div class='muted small'>{e.get('company','')}</div><br><div class='small'>{(e.get('bullets') or [''])[0]}</div></div>",unsafe_allow_html=True)

elif section == "Trayectoria":
    st.header(f"{ui(lang,'career')} · {track}")
    exp=[e for e in data.get("experience",[]) if track in e.get("tracks",[])] or data.get("experience",[])
    st.markdown("<div class='timeline'>",unsafe_allow_html=True)
    for e in exp:
        st.markdown("<div class='timeline-item'>",unsafe_allow_html=True); st.subheader(f"{e.get('role','')} · {e.get('company','')}"); st.caption(f"{e.get('period','')} · {e.get('location','')}")
        for b in e.get("bullets",[]): st.write("• "+b)
        st.markdown("</div>",unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

elif section == "Casos de proyecto":
    st.header(ui(lang,"projects")); projects=[x for x in data.get("projects",[]) if track in x.get("tracks",[])] or data.get("projects",[])
    for i in range(0,len(projects),2):
        cols=st.columns(2)
        for col,pr in zip(cols,projects[i:i+2]):
            with col:
                st.markdown(f"<div class='case'><div class='kicker'>{pr.get('sector','')} · {pr.get('region','')}</div><div class='card-title'>{pr.get('title','')}</div><div class='small'><b>{ui(lang,'role')}:</b> {pr.get('role','')} &nbsp; <b>{ui(lang,'status')}:</b> {pr.get('status','')}</div><br><div>{pr.get('summary','')}</div><br><div class='muted tiny'>{pr.get('evidence_note','')}</div></div>",unsafe_allow_html=True)

elif section == "Competencias":
    st.header(f"{ui(lang,'skills')} · {track}")
    for area,skills in data.get("skills",{}).items(): st.markdown(f"### {area}"); st.markdown(" ".join(f"`{s}`" for s in skills))
    st.divider(); st.markdown(f"### {ui(lang,'keywords')}"); st.markdown(" ".join(f"`{s}`" for s in keywords))

elif section == "Formación":
    st.header(ui(lang,"credentials"))
    for e in data.get("education",[]): st.markdown(f"### {e.get('degree','')}"); st.write(e.get("institution","") or ("Institution pending" if lang=="en" else "Institución pendiente")); st.caption(e.get("credential",""))
    if data.get("certifications"):
        st.divider(); st.subheader("Certifications" if lang=="en" else "Certificaciones / membresías")
        for c in data.get("certifications",[]): st.markdown(f"**{c.get('name','')}** — {c.get('status','')}")

elif section == "Evidencias":
    st.header(ui(lang,"evidence")); evs=[e for e in data.get("evidence",[]) if e.get("published",True)]
    if not evs: st.info(ui(lang,"no_evidence"))
    for i in range(0,len(evs),3):
        cols=st.columns(3)
        for col,ev in zip(cols,evs[i:i+3]):
            with col:
                st.markdown(f"<div class='card'><div class='kicker'>{ev.get('type','')}</div><div class='card-title'>{ev.get('title','')}</div><div class='small'>{ev.get('description','')}</div><div class='muted tiny'>{ev.get('related','')}</div></div>",unsafe_allow_html=True)
                media_render(ev)

elif section == "Match de vacante":
    st.header(ui(lang,"jobmatch")); st.caption(ui(lang,"match_note")); job=st.text_area(ui(lang,"paste_job"),height=280)
    if st.button(ui(lang,"analyze"),use_container_width=True) and job.strip():
        jt=tokenize(job); scored=[]
        for tr in tracks:
            tt=tokenize(track_text(data,tr)); overlap=jt & tt; score=(len(overlap)/max(1,len(jt)))*100; scored.append((score,tr,sorted(overlap)))
        for score,tr,overlap in sorted(scored,reverse=True):
            st.subheader(f"{tr} · {score:.0f}%"); st.write(", ".join(overlap[:30]) if overlap else "—")

elif section == "CV ATS":
    st.header(ui(lang,"resume")); ats=build_ats(data,track,lang); st.code(ats,language=None); st.download_button(ui(lang,"download"),ats.encode("utf-8"),f"Abraham_Yanez_{track.replace(' ','_').replace('/','-')}_{lang}.txt",use_container_width=True)

st.divider(); st.caption(f"Abraham Yañez Professional Hub · {datetime.now().year}")
