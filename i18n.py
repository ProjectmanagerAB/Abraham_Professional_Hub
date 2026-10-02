import re

UI = {
    "es": {
        "portfolio":"Portafolio profesional", "focus":"Enfoque profesional", "home":"Inicio",
        "career":"Trayectoria", "projects":"Casos de proyecto", "skills":"Competencias",
        "education":"Formación", "evidence":"Evidencias", "jobmatch":"Match de vacante",
        "resume":"CV ATS", "linkedin":"Ver LinkedIn", "download":"Descargar CV ATS",
        "availability":"Disponible para oportunidades", "demonstrate":"Lo que puede demostrar",
        "selected":"Perfil enfocado", "role":"Rol", "status":"Estado", "context":"Contexto",
        "responsibility":"Responsabilidad", "actions":"Acciones", "result":"Resultado",
        "proof":"Evidencia", "keywords":"Palabras clave del perfil", "credentials":"Formación y credenciales",
        "visitor_note":"Vista pública · información profesional y evidencia sanitizada",
        "language":"Idioma", "spanish":"Español", "english":"English",
        "open":"Abrir evidencia", "video":"Reproducir video", "no_evidence":"Aún no hay evidencias públicas cargadas.",
        "paste_job":"Pega aquí la descripción de la vacante", "analyze":"Analizar coincidencia",
        "match_note":"El resultado indica coincidencia de términos, no probabilidad de contratación.",
    },
    "en": {
        "portfolio":"Professional portfolio", "focus":"Professional focus", "home":"Home",
        "career":"Career", "projects":"Project cases", "skills":"Skills",
        "education":"Education", "evidence":"Evidence", "jobmatch":"Job match",
        "resume":"ATS Resume", "linkedin":"View LinkedIn", "download":"Download ATS Resume",
        "availability":"Open to opportunities", "demonstrate":"What I can demonstrate",
        "selected":"Focused profile", "role":"Role", "status":"Status", "context":"Context",
        "responsibility":"Responsibility", "actions":"Actions", "result":"Result",
        "proof":"Evidence", "keywords":"Profile keywords", "credentials":"Education and credentials",
        "visitor_note":"Public view · professional information and sanitized evidence",
        "language":"Language", "spanish":"Español", "english":"English",
        "open":"Open evidence", "video":"Play video", "no_evidence":"No public evidence has been uploaded yet.",
        "paste_job":"Paste the job description here", "analyze":"Analyze match",
        "match_note":"The result shows keyword overlap, not a probability of being hired.",
    }
}

SKIP_KEYS = {"email","phone","linkedin","url","tracks","credential","photo","period","status"}


def ui(lang, key):
    return UI.get(lang, UI["es"]).get(key, key)


def should_skip(text):
    if not isinstance(text, str):
        return True
    return bool(re.match(r"^(https?://|www\.|\+?\d|[^@\s]+@[^@\s]+\.[^@\s]+)", text.strip()))


def translate_profile(data):
    try:
        from deep_translator import GoogleTranslator
    except Exception as exc:
        raise RuntimeError("deep-translator no está instalado") from exc
    translator = GoogleTranslator(source="es", target="en")

    def rec(obj, key=None):
        if isinstance(obj, dict):
            return {k: rec(v, k) for k, v in obj.items()}
        if isinstance(obj, list):
            if key == "tracks":
                return obj[:]
            return [rec(v, key) for v in obj]
        if isinstance(obj, str):
            if key in SKIP_KEYS or should_skip(obj) or not obj.strip():
                return obj
            try:
                return translator.translate(obj)
            except Exception:
                return obj
        return obj

    result = rec(data)
    # Internal profile-track keys must remain identical so filtering still works.
    if "profile_tracks" in data:
        translated_tracks = {}
        for track_name, track_data in data["profile_tracks"].items():
            translated_tracks[track_name] = rec(track_data)
        result["profile_tracks"] = translated_tracks
    return result
