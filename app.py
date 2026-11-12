"""Abraham Professional Hub — public recruiter-first portfolio."""
import html
import re
from datetime import datetime
from urllib.parse import quote

import streamlit as st

from storage import PortfolioStore
from career_utils import load_career_history
from cv_pdf import build_cv_pdf

st.set_page_config(
    page_title="Abraham Yañez Manriquez | Proyectos y Operaciones",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {--navy:#10263c;--navy2:#193e5e;--teal:#19a4a4;--gold:#d1ad6a;--muted:#66788a;--border:#e1e8ed;}
html,body,[class*="css"] {font-family:'DM Sans',sans-serif;}
[data-testid="stAppViewContainer"]{background:#f6f8fa;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stSidebar"]{background:#10263c;}
[data-testid="stSidebar"] {background:#10263c;color:#f1f5f9;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] .stRadio label p,
[data-testid="stSidebar"] .stCaption {color:#eef5fa!important;}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:.12rem 0;}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label{border-radius:9px;padding:.45rem .55rem;}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover{background:#24445f;}
.block-container{max-width:1180px;padding-top:1.1rem;padding-bottom:3rem;}
h1,h2,h3{font-family:'Manrope',sans-serif;letter-spacing:-.035em;color:#132d43;}
h2{font-size:1.55rem!important;margin-bottom:.3rem;}
p{line-height:1.65;}
.eyebrow{font-size:.73rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:#168f92;margin-bottom:.6rem;}
.hero{background:radial-gradient(circle at 100% 0%,#286184 0%,#193d5b 38%,#10263c 85%);padding:2.6rem 2.7rem;color:white;border-radius:24px;position:relative;overflow:hidden;box-shadow:0 16px 40px rgba(16,38,60,.16);}
.hero:after{content:'';position:absolute;width:290px;height:290px;border:1px solid #ffffff22;border-radius:50%;top:-165px;right:-90px;pointer-events:none;}
.hero .eyebrow{color:#9cdddd;}
.hero h1{color:white!important;font-size:clamp(2.15rem,4vw,3.5rem);line-height:1.12;font-weight:800;margin:.25rem 0 .9rem;}
.hero h3{color:#f3f7fa!important;font-size:1.17rem;line-height:1.55;font-weight:600;margin:.3rem 0 1.1rem;}
.hero p{color:#e0eaf2;font-size:.98rem;max-width:720px;}
.hero .chip{color:#fff;border-color:#638298;background:#ffffff13;}
.chip{display:inline-block;border:1px solid #d6e1e7;border-radius:999px;padding:.36rem .72rem;margin:.16rem .27rem .16rem 0;font-size:.81rem;font-weight:600;color:#36536c;background:#fff;}
.panel{border:1px solid var(--border);background:white;padding:1.28rem 1.4rem;border-radius:16px;margin:.4rem 0 1rem;box-shadow:0 4px 22px rgba(16,38,60,.035);}
.panel h3{font-size:1.13rem!important;margin:0 0 .45rem;}
.panel .caption{color:#668092;font-size:.81rem;margin-bottom:.5rem;}
.panel p{margin:.2rem 0 .4rem;color:#40586b;font-size:.92rem;}
.panel .accent{color:#168f92;font-weight:700;font-size:.75rem;letter-spacing:.06em;text-transform:uppercase;}
.metric-card{background:#fff;border:1px solid var(--border);border-top:3px solid #19a4a4;border-radius:15px;padding:1.05rem 1.05rem;min-height:105px;margin-bottom:1rem;}
.metric-card .small{font-size:.75rem;font-weight:700;color:#6a8192;letter-spacing:.06em;text-transform:uppercase;}
.metric-card .big{font-size:1rem;font-weight:800;margin-top:.48rem;color:#15354c;line-height:1.4;}
.section-intro{color:#657b8e;margin-bottom:1.3rem;max-width:800px;}
.rule{height:1px;background:#dde5ec;margin:1.25rem 0;}
.side-name{color:#fff;font:800 1.25rem 'Manrope',sans-serif;line-height:1.3;}
.side-caption{color:#bed5e4;font-size:.85rem;margin:.5rem 0 1rem;}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:11px;min-height:44px;font-weight:700;}
.stButton>button:focus-visible,.stLinkButton>a:focus-visible{outline:3px solid #19a4a4;outline-offset:2px;}
small,.muted{color:#657a8b;}
@media(max-width:800px){.block-container{padding:.9rem .8rem 2rem;}.hero{padding:1.5rem;border-radius:17px;}.hero h1{font-size:2.05rem;}.panel{padding:1rem;}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;}}

/* Consistent high-contrast light content regardless of Streamlit theme */
[data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
  color:#1c354a !important;
}
[data-testid="stMain"] [data-testid="stMarkdownContainer"] > p,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] > div > p,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] li,
[data-testid="stMain"] .stCaption,
[data-testid="stMain"] [data-testid="stWidgetLabel"] p {
  color:#324e63 !important;
}
[data-testid="stMain"] h1,[data-testid="stMain"] h2,
[data-testid="stMain"] h3,[data-testid="stMain"] h4 {
  color:#142e44 !important;
  opacity:1 !important;
}
[data-testid="stMain"] .hero h1,[data-testid="stMain"] .hero h3 {
  color:#fff !important;
}
[data-testid="stMain"] .hero p,[data-testid="stMain"] .hero .eyebrow {
  color:#e0f0f4 !important;
}
[data-testid="stMain"] .panel h3 {color:#173b52!important;font-weight:800!important;opacity:1!important;}
[data-testid="stMain"] .panel p {color:#334e63!important;opacity:1!important;}
[data-testid="stMain"] .panel .accent {color:#087f86!important;}
[data-testid="stMain"] .section-intro {color:#586f81!important;}
[data-testid="stMain"] .metric-card .big {color:#18384f!important;}
[data-testid="stMain"] .stButton > button,
[data-testid="stMain"] .stDownloadButton > button,
[data-testid="stMain"] .stLinkButton > a {
  border:1px solid #b6cbd8!important;
  background:#fff!important;
  color:#163d58!important;
  font-weight:750!important;
}
[data-testid="stMain"] .stButton > button:hover,
[data-testid="stMain"] .stDownloadButton > button:hover,
[data-testid="stMain"] .stLinkButton > a:hover {
  border-color:#118b91!important;
  background:#e7f6f5!important;
}
[data-testid="stMain"] .stSelectbox [data-baseweb="select"] > div {
  background:#fff!important;color:#203d51!important;
}
[data-testid="stMain"] .panel {min-height:170px;display:flex;flex-direction:column;gap:.35rem;}
[data-testid="stMain"] .panel .caption {color:#647e8e!important;}
[data-testid="stMain"] .panel h3 {margin:.2rem 0 .25rem!important;line-height:1.38!important;}
[data-testid="stMain"] .panel p {line-height:1.63!important;}
[data-testid="stMain"] .stMarkdown h3 {margin-top:.7rem;}
[data-testid="stMain"] hr {border-color:#dbe5eb;}


.career-story {background:linear-gradient(145deg,#fff 0%,#f0f7f8 100%);border:1px solid #d8e5e9;border-left:5px solid #138d94;border-radius:19px;padding:2rem 2.3rem;margin:.75rem 0 2rem;box-shadow:0 8px 28px rgba(16,38,60,.055);}
[data-testid="stMain"] .career-story h2 {font-size:clamp(1.45rem,2.7vw,2rem)!important;color:#102c42!important;margin:0 0 1rem!important;line-height:1.3;}
[data-testid="stMain"] .career-story p {font-size:1rem!important;color:#365166!important;line-height:1.82!important;margin:0 0 1rem!important;max-width:980px;}
[data-testid="stMain"] .career-story .story-lead {font-size:1.12rem!important;font-weight:700!important;color:#173a52!important;}
.career-story .story-closer {font-size:1.05rem;font-weight:800;line-height:1.7;color:#0f6670;background:#dff1f0;border-radius:11px;padding:1rem 1.15rem;margin:1.1rem 0;}
.career-story .story-note {font-size:.8rem;font-weight:700;color:#607a8d;letter-spacing:.02em;}
@media(max-width:800px){.career-story{padding:1.3rem 1.15rem;}}

/* Sidebar: proper width, hierarchy, and accessible control contrast */
[data-testid="stSidebar"] {min-width:280px!important;max-width:300px!important;}
[data-testid="stSidebar"] > div:first-child {width:100%!important;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.65rem;}
[data-testid="stSidebar"] .side-name {color:#fff!important;font-size:1.18rem;line-height:1.4;}
[data-testid="stSidebar"] .side-caption {color:#c5d8e7!important;line-height:1.55;}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background:#f2f7fa!important;border:1px solid #8fa9bb!important;
  color:#12334c!important;border-radius:10px!important;min-height:45px;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] input,
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] svg {
  color:#12334c!important;fill:#12334c!important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] {gap:.25rem;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label {
  padding:.58rem .7rem!important;border-radius:10px!important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:hover {background:#234a65!important;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
  background:#1b475f!important;box-shadow:inset 3px 0 0 #39c6c5;
}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] label p {font-weight:600!important;font-size:.93rem!important;}
[data-testid="stSidebar"] .stLinkButton > a,
[data-testid="stSidebar"] .stDownloadButton > button {
  background:#f6fafc!important;border:1px solid #b8d3dd!important;
  color:#12334c!important;font-weight:800!important;border-radius:10px!important;
  min-height:44px!important;box-shadow:none!important;
}
[data-testid="stSidebar"] .stLinkButton > a *,
[data-testid="stSidebar"] .stDownloadButton > button * {
  color:#12334c!important;fill:#12334c!important;
}
[data-testid="stSidebar"] .stLinkButton > a:hover,
[data-testid="stSidebar"] .stDownloadButton > button:hover {
  background:#c7edeb!important;border-color:#2cb5b4!important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#bcd0de!important;line-height:1.55!important;}
@media(max-width:800px){[data-testid="stSidebar"]{min-width:0!important;max-width:320px!important;}}
.portfolio-art{background:linear-gradient(125deg,#10263c,#23667a);min-height:145px;border-radius:14px;padding:1.2rem;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:.4rem;color:#fff;margin-bottom:1rem}.portfolio-art span{font-size:2.8rem}.portfolio-art strong{font-weight:800;color:#e5f9fa;font-size:.88rem}.stVerticalBlockBorderWrapper{border-radius:16px!important}
[data-testid="stMain"] [data-testid="stImage"] img {border-radius:17px;box-shadow:0 10px 24px rgba(17,42,62,.12);object-fit:cover;}

/* Photo-led recruiting portfolio */
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] img{
  width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:12px;
}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] h4{color:#173c54!important;font-weight:800!important;}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] .stCaption{font-size:.76rem;color:#668296!important;}

/* Editorial collage: image-led entry point, built from local repository files. */
[data-testid="stMain"] [data-testid="stImage"] img {
    display:block;object-fit:cover;border-radius:14px;box-shadow:0 5px 16px rgba(13,37,56,.09);
}
[data-testid="stMain"] [data-testid="stCaptionContainer"] {
    margin-top:.05rem;margin-bottom:.4rem;
}
[data-testid="stMain"] [data-testid="stCaptionContainer"] p {
    color:#607d8b!important;font-size:.76rem!important;font-weight:600;
}
@media(max-width:768px){
  [data-testid="stMain"] [data-testid="stHorizontalBlock"]{gap:.65rem;}
}

/* Recruiter-friendly editorial cards: no giant generic icons */
.case-editorial {
    background:linear-gradient(125deg,#132b41 0%,#225d71 100%);
    min-height:162px;border-radius:14px;padding:1.2rem 1.35rem;
    display:flex;flex-direction:column;align-items:flex-start;justify-content:center;gap:.4rem;
}
.case-editorial span {font-size:.69rem;letter-spacing:.14em;color:#83d6d6;font-weight:800;}
.case-editorial strong {font-size:1.12rem;line-height:1.4;font-weight:800;color:#ffffff;}
.case-editorial small {font-size:.64rem;color:#bad6df;letter-spacing:.12em;}
.case-kicker {color:#087d87;font-weight:800;letter-spacing:.08em;font-size:.73rem;
    text-transform:uppercase;padding-top:.3rem;}
.story-count {color:#67818f;font-size:.82rem;font-weight:700;margin:-.25rem 0 .6rem;}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] h4 {margin:.4rem 0!important;}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] img {
    width:100%;aspect-ratio:1.3;object-fit:cover;border-radius:11px;
}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] p {
    font-size:.71rem!important;line-height:1.4!important;
}
[data-testid="stMain"] [data-testid="stExpander"] {border:1px solid #d9e5e9;border-radius:10px;}

.album-kicker{font-weight:800;font-size:.73rem;letter-spacing:.11em;color:#07868a;margin:.3rem 0;}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] img{aspect-ratio:1.85;object-fit:cover;border-radius:13px;}
[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] h4{color:#17384e!important;font-weight:800!important;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


PORTFOLIO_SHOWCASE = [["Ingeniería de agua y ósmosis","Water engineering and reverse osmosis","Agua e infraestructura","Water and infrastructure","Coordinación de equipos, contratistas, compras, cronogramas y sistemas de tratamiento de agua para infraestructura hotelera.","Coordination of equipment, contractors, procurement, schedules and water treatment systems for hospitality infrastructure.","💧"],["Rehabilitación de plantas y sistemas UV","Plant rehabilitation and UV systems","Rehabilitación técnica","Technical rehabilitation","Seguimiento a reparaciones, inspecciones, componentes, instalaciones hidráulicas y verificación de alcances técnicos.","Follow-up on repairs, inspections, components, hydraulic installations and technical scope.","🔧"],["Trigeneración y sistemas electromecánicos","Trigeneration and electromechanical systems","Energía","Energy","Coordinación documental, responsabilidades, suministros y seguimiento de interfaces entre generación, enfriamiento y sistemas auxiliares.","Coordination of documents, responsibilities, supplies and interfaces across generation, cooling and auxiliary systems.","⚡"],["Robótica de soldadura","Robotic welding","Automatización industrial","Industrial automation","Implementación técnica de celda UR10 y soldadura Fronius 320i en manufactura metalmecánica.","Technical implementation of UR10 robotic cell and Fronius 320i welding in metalworking.","🦾"],["Pintura electrostática y mejora de procesos","Electrostatic coating and process improvement","Manufactura","Manufacturing","Instalación y puesta en marcha de línea industrial, con enfoque en integración y continuidad de producción.","Installation and startup of an industrial line, focused on integration and production continuity.","🏭"],["Producción, maquinaria y operaciones","Production, machinery and operations","Operaciones industriales","Industrial operations","Experiencia coordinando procesos de maquinado, soldadura, troquelado, planeación, KPIs y proveedores.","Experience coordinating machining, welding, stamping, planning, KPIs and suppliers.","⚙️"],["Logística de proyectos internacionales","International project logistics","Supply chain","Supply chain","Gestión y seguimiento de materiales, entregas, fletes y documentación entre México y el Caribe.","Tracking materials, deliveries, freight and documentation across Mexico and the Caribbean.","🚢"],["Digitalización, PMO y control operativo","Digitalization, PMO and operational controls","Transformación digital","Digital transformation","Implementación de ERP, Monday, herramientas de seguimiento de actividades, compras, costos y documentación.","ERP, Monday and activity, procurement, cost and documentation tracking tools.","📊"],["Desarrollo técnico-comercial","Technical-commercial development","Comercial e ingeniería","Sales and engineering","Vinculación entre necesidades industriales, proveedores de herramentales, especificaciones y propuestas de solución.","Connecting industrial needs, tooling suppliers, specifications and solution proposals.","🤝"],["Capacitación empresarial y consultoría","Corporate training and consulting","Formación de equipos","Team development","Diseño e impartición de contenidos para empresas, procesos de mejora continua y competencias profesionales.","Design and delivery of corporate content, continuous improvement and professional skills.","🎓"],["Docencia y acompañamiento formativo","Teaching and educational guidance","Docencia","Education","Experiencia impartiendo administración, finanzas, marco legal y otras materias; tutoría y acompañamiento a estudiantes.","Teaching management, finance, legal frameworks and related subjects; student tutoring and guidance.","📚"],["Movimiento y maniobras de equipos industriales","Industrial equipment movement and handling","Ejecución y logística industrial","Industrial execution and logistics","La coordinación de los proyectos no termina en la compra: incluye preparar accesos, movimientos, recursos y entregas de equipos voluminosos en planta.","Project delivery extends beyond purchasing: it includes access planning, equipment movement, resources and heavy-equipment delivery on site.","🏗️"],["Interfaces de obra e instalaciones","Site interfaces and installation works","Infraestructura","Infrastructure","Experiencia profesional en coordinación de frentes de instalación y servicios técnicos en ambientes de obra.","Professional experience coordinating installation workstreams and technical services in construction settings.","🏢"]]

SHOWCASE_IMAGES = {
    6: "assets/project_container_loading.svg",
    9: "assets/portfolio_classroom_archive.svg",
    10: "assets/portfolio_group_training.svg",
    11: "assets/project_equipment_movement.svg",
    12: "assets/portfolio_field_execution.svg",
}
SHOWCASE_PHOTO_NOTES = {
    6: ("Archivo real: carga y embalaje de equipo en contenedor. Proyecto específico no acreditado.",
        "Real archive: equipment loading and packaging inside container. Specific project not established."),
    9: ("Archivo real de actividad formativa. No se publican nombres ni se acredita la autoría de la sesión solo por la fotografía.",
        "Real training activity archive. Participants are unnamed; the photo alone does not prove who delivered the session."),
    10: ("Archivo real de una actividad grupal formativa; sin identificación de participantes.",
         "Real archive of a group learning activity; participants are not identified."),
    11: ("Archivo real de maniobra de equipo en planta. No se identifica cliente.",
         "Real archive of on-site equipment handling. Client not identified."),
    12: ("Archivo real de frente de trabajo en instalación; contexto de obra no verificado.",
         "Real archive of an installation work area; specific project context not verified."),
}
# Curated real-photo editorial mosaic. Captions describe what is visible,
# not a claim of personal authorship, outcome or client affiliation.

@st.cache_data(show_spinner=False)
def load_album_cases():
    import json
    from pathlib import Path
    path = Path(__file__).parent / "assets" / "album_stories.json"
    return json.loads(path.read_text(encoding="utf-8"))


def render_album_case(item, language, preview=False):
    title = item["title_en"] if language == "en" else item["title"]
    with st.container(border=True):
        st.image("assets/albums/" + item["slug"] + ".svg", use_container_width=True)
        st.markdown('<div class="album-kicker">' + esc(item["tag"]) + '</div>', unsafe_allow_html=True)
        st.markdown("#### " + title)
        if language == "es":
            st.markdown("**" + item["lead"] + "**")
            if not preview:
                st.markdown("**El reto.** " + item["challenge"])
                st.markdown("**Mi experiencia.** " + item["role"])
        else:
            st.markdown("**Selected project experience.**")
            if not preview:
                st.write(item["role"])
        if not preview:
            with st.expander("Sobre las imágenes" if language == "es" else "About the images"):
                st.caption("Imágenes del álbum original facilitado por el titular. Las imágenes de ingeniería pueden ser modelos o renders; no todas representan instalaciones terminadas."
                           if language == "es" else
                           "Original album imagery supplied by the owner. Engineering visualizations may be models, not completed installations.")


PHOTO_GALLERY = [
    ("assets/project_equipment_handling.svg", "Maniobras de maquinaria", "Industrial equipment handling"),
    ("assets/portfolio_field_execution.svg", "Instalaciones y obra", "Field installations"),
    ("assets/portfolio_classroom_archive.svg", "Capacitación de equipos", "Team training"),
    ("assets/project_container_loading.svg", "Equipos y embarques", "Equipment shipments"),
    ("assets/portfolio_group_training.svg", "Formación y personas", "People development"),
    ("assets/project_equipment_movement.svg", "Ejecución industrial", "Industrial execution"),
    ("assets/portfolio_technical_facility.svg", "Infraestructura técnica", "Technical infrastructure"),
]


def gallery_collage(language, include_heading=True):
    if include_heading:
        st.markdown("### " + ("Proyectos reales en imágenes" if language == "es" else "Projects in pictures"))
        st.caption("Selección de álbumes originales de ingeniería, manufactura, tratamiento de agua y formación."
                   if language == "es" else
                   "Selected original albums from engineering, manufacturing, water treatment and training.")
    all_items = load_album_cases()
    picks = [2, 0, 7, 5, 1, 4]
    cols = st.columns(3, gap="small")
    for i, index in enumerate(picks):
        item = all_items[index]
        with cols[i % 3]:
            st.image("assets/albums/" + item["slug"] + ".svg", use_container_width=True)
            st.caption(item["title_en"] if language == "en" else item["title"])


CASE_STORIES = {
  0: {
    "es": ("El reto: coordinar disciplinas, compras, espacios y contratistas en proyectos de tratamiento de agua.",
           "Mi participación: planeación técnica, suministros, logística, supervisión y seguimiento a las necesidades del cliente.",
           "Lo que demuestra: capacidad para organizar sistemas complejos y mantener informadas a distintas partes."),
    "en": ("The challenge: coordinate disciplines, purchases, site constraints and contractors in water treatment projects.",
           "My role: technical planning, supplies, logistics, supervision and customer requirements follow-up.",
           "What it shows: an ability to organize complex systems and keep different stakeholders aligned.")},
  3: {
    "es": ("El reto: incorporar automatización de soldadura en un proceso industrial existente.",
           "Mi participación: implementación de celda UR10 con equipo Fronius 320i y coordinación con operación.",
           "Lo que demuestra: comprensión práctica de la integración entre tecnología y producción."),
    "en": ("The challenge: bring robotic welding into an existing industrial operation.",
           "My role: UR10 cell implementation with Fronius 320i welding and production coordination.",
           "What it shows: practical integration of technology and production.")},
  6: {
    "es": ("El reto: gestionar equipos y materiales entre proveedores, transporte y condiciones de recepción.",
           "Mi participación: seguimiento de abastecimiento, entregas, documentación y recursos de maniobra.",
           "Lo que demuestra: enfoque logístico orientado a que el material llegue listo para la ejecución."),
    "en": ("The challenge: coordinate equipment and materials from suppliers through transport and receiving conditions.",
           "My role: procurement, delivery, documentation and handling coordination.",
           "What it shows: delivery-focused logistics that supports site execution.")},
  9: {
    "es": ("El reto: adaptar la formación a las necesidades operativas y humanas de cada organización.",
           "Mi participación: instrucción y consultoría empresarial en competencias técnicas y habilidades de gestión.",
           "Lo que demuestra: facilidad para comunicar conocimientos y promover aprendizaje aplicado."),
    "en": ("The challenge: adapt learning to each organization's operational and people needs.",
           "My role: corporate training and consulting in technical and management capabilities.",
           "What it shows: communication and applied learning facilitation.")},
  11: {
    "es": ("El reto: mover equipos de gran volumen dentro de espacios de trabajo, cuidando recursos y coordinación.",
           "Mi participación: experiencia vinculada a coordinación industrial y logística de equipos.",
           "Lo que demuestra: atención a la ejecución física, no solo a la planeación."),
    "en": ("The challenge: move large equipment through working environments with careful resource coordination.",
           "My role: experience supporting industrial equipment handling and logistics coordination.",
           "What it shows: attention to physical execution rather than plans alone.")},
  12: {
    "es": ("El reto: integrar actividades de instalación con otros frentes de trabajo e instalaciones existentes.",
           "Mi contribución profesional: coordinación y seguimiento de actividades en entornos de infraestructura.",
           "Lo que demuestra: entendimiento de interfaces entre especialidades y condiciones de obra."),
    "en": ("The challenge: integrate installation activities with other workstreams and existing facilities.",
           "My professional contribution: coordination and follow-up in infrastructure contexts.",
           "What it shows: understanding interfaces between trades and site constraints.")},
}

def esc(value):
    return html.escape(str(value or ""), quote=True)


def phone_link(number, lang):
    digits = re.sub(r"\D", "", number or "")
    if len(digits) == 10:
        digits = "52" + digits
    if not digits:
        return ""
    message = ("Hello Abraham, I reviewed your portfolio and would like to discuss a career opportunity."
               if lang == "en" else
               "Hola Abraham, revisé tu portafolio y me gustaría conversar sobre una oportunidad laboral.")
    return "https://wa.me/" + digits + "?text=" + quote(message)


def panel(title, desc, eyebrow="", meta=""):
    st.markdown(
        '<div class="panel">'
        + (f'<div class="accent">{esc(eyebrow)}</div>' if eyebrow else "")
        + f'<h3>{esc(title)}</h3>'
        + (f'<div class="caption">{esc(meta)}</div>' if meta else "")
        + f'<p>{esc(desc)}</p></div>',
        unsafe_allow_html=True,
    )


def heading(title, intro):
    st.markdown("## " + title)
    st.markdown(f'<p class="section-intro">{esc(intro)}</p>', unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def read_profile(language):
    return PortfolioStore().load(language)


language = st.sidebar.selectbox("Idioma / Language", ["Español", "English"], index=0)
lang = "en" if language == "English" else "es"
data = read_profile(lang) or read_profile("es")
p = data.get("personal", {})
name = p.get("name") or "Abraham Yañez Manriquez"
projects = [x for x in data.get("projects", []) if x.get("published", True)]
experience = [x for x in data.get("experience", []) if x.get("published", True)]
for historical in load_career_history():
    if not any(x.get("company", "").casefold() == historical.get("company", "").casefold() for x in experience):
        experience.append({
            "company": historical.get("company", ""),
            "role": historical.get("role", ""),
            "period": historical.get("period", ""),
            "location": "México" if lang == "es" else "Mexico",
            "bullets": [historical.get("summary", "")],
        })
whatsapp = phone_link(p.get("phone", ""), lang)
tracks = list(data.get("profile_tracks", {}).keys()) or ["Project Manager"]

T = {
    "es": {
        "sections": ["Inicio", "Experiencia", "Proyectos", "Competencias", "Formación", "Contacto"],
        "position": "Liderazgo de proyectos industriales y operaciones",
        "subtitle": "Ingeniería • Manufactura • Agua y energía • Implementación internacional",
        "availability": "Disponible para nuevas oportunidades profesionales",
        "overview": "Proyectos, operaciones y soluciones técnicas con visión de negocio.",
        "value": "Áreas donde puedo aportar valor",
        "value_intro": "Experiencia técnica combinada con coordinación operativa, comercial y de proveedores.",
        "experience": "Experiencia profesional",
        "experience_intro": "Una trayectoria en ejecución de proyectos, producción, industria y formación técnica.",
        "projects": "Proyectos destacados",
        "projects_intro": "Ejemplos representativos de implementación y coordinación. Se omite información confidencial.",
        "skills": "Competencias y herramientas",
        "skills_intro": "Capacidades aplicadas a proyectos técnicos, operaciones y mejora continua.",
        "education": "Formación y desarrollo",
        "education_intro": "Preparación académica y competencias profesionales.",
        "contact": "Conversemos sobre tu vacante",
        "contact_intro": "Abierto a posiciones de gerencia, coordinación y ejecución de proyectos, operaciones y manufactura.",
        "download": "Descargar CV PDF",
        "linked": "LinkedIn",
        "message": "WhatsApp",
        "mail": "Correo electrónico",
        "career": "Ver experiencia",
        "cases": "Explorar proyectos",
        "mobility": "Movilidad nacional e internacional",
        "track": "Personaliza el CV para una posición",
        "track_note": "Elige un puesto objetivo para descargar un CV ejecutivo en PDF, con texto seleccionable y estructura compatible con ATS.",
        "evidence": "Evidencia pública",
        "evidence_empty": "Las evidencias visuales se incorporarán cuando existan materiales autorizados para publicación.",
        "closing": "Transformar planes técnicos en ejecución coordinada.",
    },
    "en": {
        "sections": ["Home", "Experience", "Projects", "Skills", "Education", "Contact"],
        "position": "Industrial projects and operations leadership",
        "subtitle": "Engineering • Manufacturing • Water and energy • International implementation",
        "availability": "Open to new career opportunities",
        "overview": "Projects, operations and technical solutions with a business mindset.",
        "value": "Where I bring value",
        "value_intro": "Technical experience combined with operational, commercial and supplier coordination.",
        "experience": "Professional experience",
        "experience_intro": "A background spanning project execution, manufacturing, industry and technical education.",
        "projects": "Selected projects",
        "projects_intro": "Representative implementation and coordination cases. Confidential details are excluded.",
        "skills": "Skills and tools",
        "skills_intro": "Capabilities applied to technical projects, operations and continuous improvement.",
        "education": "Education and development",
        "education_intro": "Academic qualifications and professional capabilities.",
        "contact": "Let's discuss your opportunity",
        "contact_intro": "Open to management, coordination and delivery roles in projects, operations and manufacturing.",
        "download": "Download PDF resume",
        "linked": "LinkedIn",
        "message": "WhatsApp",
        "mail": "Email",
        "career": "View experience",
        "cases": "Explore projects",
        "mobility": "Available for domestic and international relocation",
        "track": "Tailor the resume to a role",
        "track_note": "Choose a target role to download an executive PDF resume with selectable, ATS-readable text.",
        "evidence": "Public evidence",
        "evidence_empty": "Visual evidence will be added once materials are authorized for publication.",
        "closing": "Turning technical plans into coordinated execution.",
    },
}[lang]

def change_page(index):
    st.session_state["page_nav"] = T["sections"][index]


with st.sidebar:
    st.markdown(f'<div class="side-name">{esc(name)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="side-caption">{esc(T["position"])}</div>', unsafe_allow_html=True)
    selected = st.radio("Navigation" if lang == "en" else "Navegación", T["sections"], label_visibility="collapsed", key="page_nav")
    st.divider()
    if p.get("linkedin"):
        st.link_button("LinkedIn", p["linkedin"], use_container_width=True)
    if whatsapp:
        st.link_button("WhatsApp", whatsapp, use_container_width=True)
    st.download_button(T["download"], build_cv_pdf(data, lang), "Abraham_Yanez_CV_" + lang + ".pdf",
                       mime="application/pdf", use_container_width=True)
    st.caption(T["mobility"])

section = T["sections"].index(selected)

if section == 0:
    hero_left, hero_right = st.columns([3.4, 1], gap="large")
    with hero_left:
        tags = ["Project Management", "Operations", "Manufacturing", "Water & Energy"]
        chips = "".join(f'<span class="chip">{esc(item)}</span>' for item in tags)
        st.markdown(
            f'<section class="hero"><div class="eyebrow">{esc(T["availability"])}</div>'
            f'<h1>{esc(name)}</h1>'
            f'<h3>{esc(T["position"])}</h3>'
            f'<p>{esc(T["overview"])} {esc(T["subtitle"])}</p>'
            f'<div>{chips}</div></section>', unsafe_allow_html=True,
        )
        btn1, btn2, btn3 = st.columns(3)
        btn1.button(T["career"], use_container_width=True, on_click=change_page, args=(1,))
        btn2.button(T["cases"], use_container_width=True, on_click=change_page, args=(2,))
        btn3.download_button(T["download"], build_cv_pdf(data, lang),
                             "Abraham_Yanez_CV_" + lang + ".pdf",
                             mime="application/pdf", use_container_width=True)
    with hero_right:
        # Authentic profile photograph extracted from the user's own CV.
        # An explicitly configured profile photo takes precedence.
        profile_photo = p.get("photo") or "assets/profile_photo.svg"
        st.image(profile_photo, use_container_width=True)

        st.markdown("**" + p.get("location", "") + "**")
        st.caption(p.get("mobility", T["mobility"]))
    st.write("")
    gallery_collage(lang)
    st.write("")
    metrics = [
        ("Industria" if lang == "es" else "Industry", "Manufactura / Manufacturing"),
        ("Proyectos" if lang == "es" else "Projects", "México + Caribe" if lang == "es" else "Mexico + Caribbean"),
        ("Especialidad" if lang == "es" else "Specialty", "Agua, energía, automatización" if lang == "es" else "Water, energy, automation"),
        ("Enfoque" if lang == "es" else "Focus", "Operaciones + PMO" if lang == "es" else "Operations + PMO"),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, metrics):
        col.markdown(f'<div class="metric-card"><div class="small">{esc(label)}</div>'
                     f'<div class="big">{esc(value)}</div></div>', unsafe_allow_html=True)
    # Executive narrative: present a clear career progression before the value areas.
    if lang == "es":
        story_title = "De la ingeniería a la dirección de proyectos"
        story_lead = "Mi trayectoria se ha construido donde los planes tienen que convertirse en resultados: en la operación, en la planta y frente a los retos reales de cada proyecto."
        story_body = (
            "Comencé desarrollando experiencia en procesos industriales, manufactura y coordinación técnica. "
            "Ese contacto directo con la producción me enseñó que una buena solución no depende únicamente de la ingeniería: "
            "requiere personas alineadas, proveedores confiables, recursos disponibles y decisiones oportunas."
        )
        story_body_two = (
            "Con el tiempo asumí responsabilidades en gestión de producción, automatización y mejora continua: "
            "desde la implementación de soldadura robótica y líneas de pintura electrostática hasta herramientas de control y seguimiento operativo. "
            "Hoy aplico esa visión integral a proyectos de infraestructura y tratamiento de agua vinculados con México y el Caribe, "
            "coordinando actividades técnicas, contratistas, suministros y necesidades del cliente."
        )
        story_finish = (
            "Mi fortaleza es conectar la estrategia con la ejecución: entender el problema, ordenar las prioridades "
            "y dar seguimiento a los compromisos para que el proyecto avance."
        )
        story_note = "Ingeniería en Gestión de Proyectos · Maestría en Administración Estratégica"
    else:
        story_title = "From engineering to project leadership"
        story_lead = "My career has grown where plans must become results: on the shop floor, in operations, and in the face of real project challenges."
        story_body = (
            "I developed my foundations in industrial processes, manufacturing and technical coordination. "
            "Hands-on exposure to production taught me that a sound solution depends on more than engineering: "
            "it takes aligned people, reliable suppliers, available resources and timely decisions."
        )
        story_body_two = (
            "I went on to take responsibility for production management, automation and continuous improvement, "
            "including robotic welding implementation, electrostatic coating lines and operational tracking tools. "
            "Today I bring that perspective to infrastructure and water-treatment projects involving Mexico and the Caribbean, "
            "coordinating technical work, contractors, procurement and customer needs."
        )
        story_finish = (
            "My strength lies in connecting strategy with execution: understanding the challenge, setting priorities "
            "and following through on commitments to keep projects moving."
        )
        story_note = "Engineering in Project Management · Master's in Strategic Management"
    st.markdown(
        '<section class="career-story">'
        '<div class="eyebrow">PROFILE / PERFIL PROFESIONAL</div>'
        f'<h2>{esc(story_title)}</h2>'
        f'<p class="story-lead">{esc(story_lead)}</p>'
        f'<p>{esc(story_body)}</p>'
        f'<p>{esc(story_body_two)}</p>'
        f'<div class="story-closer">{esc(story_finish)}</div>'
        f'<div class="story-note">{esc(story_note)}</div>'
        '</section>',
        unsafe_allow_html=True,
    )
    heading(T["value"], T["value_intro"])
    areas = [
        ("01 · Project Management", "Planeación, control de costos, riesgos, proveedores y coordinación de contratistas."
         if lang == "es" else "Planning, cost and risk control, suppliers and contractor coordination."),
        ("02 · Industrial Operations", "Producción, mejora continua, KPIs y desarrollo de procesos metalmecánicos."
         if lang == "es" else "Production, continuous improvement, KPIs and metalworking process development."),
        ("03 · Water & Energy", "Proyectos de tratamiento de agua e infraestructura técnica en entornos internacionales."
         if lang == "es" else "Water treatment and technical infrastructure projects in international settings."),
        ("04 · Digital & Supply Chain", "ERP, seguimiento, compras, logística y desarrollo de proveedores."
         if lang == "es" else "ERP, tracking, procurement, logistics and supplier development."),
    ]
    for i in range(0, len(areas), 2):
        cols = st.columns(2)
        for col, (title, desc) in zip(cols, areas[i:i+2]):
            with col:
                panel(title, desc)
    st.markdown("### " + ("Conoce los proyectos detrás de las imágenes" if lang == "es" else "Explore the stories behind the pictures"))
    st.caption("Selecciona Proyectos para conocer responsabilidades y experiencias por especialidad." if lang == "es"
               else "Visit Projects to explore responsibilities and experience by specialty.")
    st.button("Explorar portafolio completo" if lang == "es" else "Explore full portfolio",
              on_click=change_page, args=(2,), use_container_width=True)

elif section == 1:
    heading(T["experience"], T["experience_intro"])
    for item in experience:
        panel(item.get("role"), " · ".join(str(x) for x in item.get("bullets", [])[:3]),
              item.get("company"), " | ".join(filter(None, [item.get("period"), item.get("location")])))

elif section == 2:
    heading(
        "Experiencia que se puede ver" if lang == "es" else "Experience you can see",
        "Nueve álbumes originales, fotografías reales y relatos claros sobre el valor de coordinar proyectos."
        if lang == "es" else "Nine original albums with photographs and concise project narratives."
    )
    groups = (["Todos", "Agua e infraestructura", "Manufactura", "Capacitación y docencia"]
              if lang == "es" else ["All", "Water infrastructure", "Manufacturing", "Training and teaching"])
    group = st.selectbox("Filtrar proyectos" if lang == "es" else "Filter projects", groups)
    category = [None, "water", "industrial", "people"][groups.index(group)]
    items = [item for item in load_album_cases() if category is None or item["group"] == category]
    for index in range(0, len(items), 2):
        columns = st.columns(2, gap="medium")
        for col, item in zip(columns, items[index:index+2]):
            with col:
                render_album_case(item, lang)
    st.divider()
    st.markdown("### " + ("¿Tu empresa necesita liderazgo de proyectos?" if lang == "es"
                         else "Looking for project leadership?"))
    st.write("Ingeniería, operaciones, manufactura y formación reunidas en una trayectoria profesional."
             if lang == "es" else "Engineering, operations, manufacturing and training throughout a professional career.")
    st.button("Contactar para entrevista" if lang == "es" else "Contact for interview",
              on_click=change_page, args=(5,), use_container_width=True)

elif section == 3:
    heading(T["skills"], T["skills_intro"])
    for group, items in data.get("skills", {}).items():
        with st.container(border=True):
            st.markdown("#### " + group)
            st.markdown("".join(f'<span class="chip">{esc(value)}</span>' for value in items),
                        unsafe_allow_html=True)

elif section == 4:
    heading(T["education"], T["education_intro"])
    for ed in data.get("education", []):
        panel(ed.get("degree"), ed.get("institution", ""), meta=ed.get("credential", ""))
    certs = [c for c in data.get("certifications", []) if c.get("published", True)]
    if certs:
        st.markdown("### " + ("Certificaciones y membresías" if lang == "es" else "Certificates and memberships"))
        for cert in certs:
            panel(cert.get("name"), cert.get("status"))

elif section == 5:
    heading(T["contact"], T["contact_intro"])
    st.markdown(f'<div class="hero"><div class="eyebrow">Contact / Contacto</div>'
                f'<h1>{esc(T["closing"])}</h1><p>{esc(T["mobility"])}</p></div>',
                unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns(3)
    if whatsapp:
        c1.link_button(T["message"], whatsapp, use_container_width=True)
    if p.get("email"):
        c2.link_button(T["mail"], "mailto:" + quote(p["email"], safe="@."),
                       use_container_width=True)
    if p.get("linkedin"):
        c3.link_button(T["linked"], p["linkedin"], use_container_width=True)
    st.download_button(T["download"], build_cv_pdf(data, lang),
                       "Abraham_Yanez_CV_" + lang + ".pdf",
                       mime="application/pdf", use_container_width=True)
    st.markdown("### " + T["track"])
    st.caption(T["track_note"])
    track = st.selectbox("Target role" if lang == "en" else "Puesto objetivo", tracks)
    st.download_button(T["download"] + " · " + track, build_cv_pdf(data, lang, track),
                       "Abraham_Yanez_" + re.sub(r"[^a-zA-Z0-9_-]", "_", track) + ".pdf",
                       mime="application/pdf", use_container_width=True)

st.divider()
st.caption(f"Abraham Yañez Manriquez · Professional Hub · {datetime.now().year} · "
           + ("Portfolio for recruiters" if lang == "en" else "Portafolio para reclutadores"))
