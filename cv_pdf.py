"""Professional recruiter-ready PDF resume, generated from the published profile."""
from io import BytesIO
from html import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)

NAVY = colors.HexColor("#102A40")
TEAL = colors.HexColor("#087F86")
MUTED = colors.HexColor("#557083")
LIGHT = colors.HexColor("#E3ECEF")
PALE = colors.HexColor("#F2F7F8")


def _safe(value):
    """Remove unsafe markup while preserving accents and newlines."""
    return escape(str(value or "")).replace("\n", "<br/>")


def _styles():
    return {
        "name": ParagraphStyle("CVName", fontName="Helvetica-Bold", fontSize=21, leading=24, textColor=NAVY, spaceAfter=5),
        "headline": ParagraphStyle("CVHeadline", fontName="Helvetica-Bold", fontSize=10, leading=14, textColor=TEAL, spaceAfter=5),
        "contact": ParagraphStyle("CVContact", fontName="Helvetica", fontSize=8, leading=11.8, textColor=MUTED, wordWrap="CJK"),
        "section": ParagraphStyle("CVSection", fontName="Helvetica-Bold", fontSize=10.1, leading=14, textColor=NAVY, spaceBefore=13, spaceAfter=6),
        "body": ParagraphStyle("CVBody", fontName="Helvetica", fontSize=8.7, leading=12.9, textColor=NAVY, spaceAfter=4),
        "role": ParagraphStyle("CVRole", fontName="Helvetica-Bold", fontSize=9.1, leading=12.5, textColor=NAVY),
        "meta": ParagraphStyle("CVMeta", fontName="Helvetica", fontSize=7.8, leading=11, textColor=MUTED, spaceAfter=4),
        "bullet": ParagraphStyle("CVBullet", fontName="Helvetica", fontSize=8.15, leading=11.7, leftIndent=10, firstLineIndent=-8, textColor=NAVY, spaceAfter=2),
        "skill": ParagraphStyle("CVSkill", fontName="Helvetica", fontSize=8.1, leading=12, textColor=NAVY),
    }


def build_cv_pdf(profile, language="es", track=None):
    """Return an in-memory, selectable-text PDF. Only use published profile content."""
    p = profile.get("personal", {}) or {}
    english = language == "en"
    T = (
        {"profile": "PROFESSIONAL PROFILE", "experience": "PROFESSIONAL EXPERIENCE",
         "projects": "SELECTED PROJECTS", "skills": "CORE COMPETENCIES",
         "education": "EDUCATION", "mobility": "Mobility", "page": "Page"}
        if english else
        {"profile": "PERFIL EJECUTIVO", "experience": "EXPERIENCIA PROFESIONAL",
         "projects": "PROYECTOS DESTACADOS", "skills": "COMPETENCIAS CLAVE",
         "education": "FORMACIÓN ACADÉMICA", "mobility": "Movilidad", "page": "Página"}
    )
    sty = _styles()
    output = BytesIO()
    pdf = SimpleDocTemplate(
        output, pagesize=A4,
        topMargin=18*mm, bottomMargin=17*mm,
        leftMargin=19*mm, rightMargin=19*mm,
        title=str(p.get("name", "Abraham Yañez Manriquez")) + " | CV",
        author=str(p.get("name", "Abraham Yañez Manriquez")),
        subject="Professional resume" if english else "Currículum profesional",
        pageCompression=1,
    )
    story = []
    story.append(Paragraph(_safe(p.get("name", "Abraham Yañez Manriquez")), sty["name"]))
    title = track or p.get("headline") or "Project Management | Operations"
    story.append(Paragraph(_safe(title), sty["headline"]))
    contacts = [p.get("location"), p.get("email"), p.get("phone")]
    story.append(Paragraph(_safe("   |   ".join(str(v) for v in contacts if v)), sty["contact"]))
    if p.get("linkedin"):
        story.append(Paragraph(_safe(p["linkedin"]), sty["contact"]))
    story.append(Spacer(1, 7))
    story.append(HRFlowable(width="100%", thickness=1.7, color=TEAL))
    def section(text):
        story.append(Paragraph(_safe(text), sty["section"]))
    section(T["profile"])
    story.append(Paragraph(_safe(p.get("summary", "")), sty["body"]))

    if p.get("mobility"):
        story.append(Paragraph("<b>" + T["mobility"] + ":</b> " + _safe(p["mobility"]), sty["body"]))

    section(T["experience"])
    jobs = [x for x in profile.get("experience", []) if x.get("published", True)]
    # Tailor ordering to the selected role without erasing the rest of the career history.
    if track:
        jobs.sort(key=lambda x: track not in x.get("tracks", []))
    for job in jobs[:8]:
        header = Paragraph(_safe(job.get("role", "")) + "  |  " + _safe(job.get("company", "")), sty["role"])
        details = "  |  ".join(str(x) for x in [job.get("period"),job.get("location")] if x)
        block = [header, Paragraph(_safe(details), sty["meta"])]
        for item in (job.get("bullets") or [])[:3]:
            block.append(Paragraph("- " + _safe(item), sty["bullet"]))
        block.append(Spacer(1, 5))
        story.append(KeepTogether(block))

    projects = [x for x in profile.get("projects", []) if x.get("published", True)]
    if track:
        projects.sort(key=lambda x: track not in x.get("tracks", []))
    if projects:
        section(T["projects"])
        for item in projects[:4]:
            block = [
                Paragraph(_safe(item.get("title", "")), sty["role"]),
                Paragraph(_safe(item.get("summary", "")), sty["body"]),
                Spacer(1, 4),
            ]
            story.append(KeepTogether(block))

    skill_groups = profile.get("skills", {}) or {}
    if skill_groups:
        section(T["skills"])
        # Compact and parseable: no charts, columns or image-only text.
        for group, values in list(skill_groups.items())[:7]:
            if not isinstance(values, list):
                continue
            story.append(Paragraph(
                "<b>" + _safe(group) + ":</b> " + _safe(", ".join(map(str, values[:11]))),
                sty["skill"]
            ))

    education = profile.get("education", []) or []
    if education:
        section(T["education"])
        for item in education[:5]:
            degree = item.get("degree", "")
            institution = item.get("institution", "")
            line = degree + ((" | " + institution) if institution else "")
            story.append(Paragraph(_safe(line), sty["body"]))

    def decorate(canv, doc):
        canv.saveState()
        w, h = A4
        canv.setStrokeColor(LIGHT)
        canv.setLineWidth(.7)
        canv.line(19*mm, 14*mm, w-19*mm, 14*mm)
        canv.setFont("Helvetica", 7.3)
        canv.setFillColor(MUTED)
        canv.drawString(19*mm, 10.5*mm, "ABRAHAM YAÑEZ MANRIQUEZ  /  CV")
        canv.drawRightString(w-19*mm, 10.5*mm, T["page"] + " " + str(doc.page))
        canv.restoreState()

    pdf.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return output.getvalue()
