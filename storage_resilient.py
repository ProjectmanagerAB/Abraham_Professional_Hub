import json
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
import streamlit as st

BASE = Path(__file__).parent
ES_FILE = BASE / "profile_data.json"
EN_FILE = BASE / "profile_data_en.json"
UPLOADS = BASE / "assets" / "uploads"


def _secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def _valid_supabase_url(value: str) -> bool:
    if not value:
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


class PortfolioStore:
    def __init__(self):
        self.url = (_secret("SUPABASE_URL") or "").strip().rstrip("/")
        self.key = (_secret("SUPABASE_SERVICE_KEY") or "").strip()
        self.bucket = (_secret("SUPABASE_BUCKET", "portfolio-media") or "portfolio-media").strip()
        self.remote = bool(_valid_supabase_url(self.url) and self.key)
        self.last_error = None

    @property
    def mode(self):
        return "Supabase" if self.remote else "Local JSON"

    def _headers(self, extra=None):
        h = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def _local_load(self, lang="es"):
        file = ES_FILE if lang == "es" else EN_FILE
        if file.exists():
            return json.loads(file.read_text(encoding="utf-8"))
        if lang != "es":
            return self._local_load("es")
        return {}

    def load(self, lang="es"):
        row_key = f"profile_{lang}"
        if self.remote:
            try:
                endpoint = f"{self.url}/rest/v1/portfolio_state"
                r = requests.get(
                    endpoint,
                    params={"key": f"eq.{row_key}", "select": "content"},
                    headers=self._headers(),
                    timeout=20,
                )
                r.raise_for_status()
                rows = r.json()
                if rows:
                    self.last_error = None
                    return rows[0]["content"]
            except requests.RequestException as exc:
                self.last_error = f"Supabase read failed: {exc}"
                # Public portfolio must remain available even if Supabase is unavailable.
        return self._local_load(lang)

    def save(self, data, lang="es"):
        row_key = f"profile_{lang}"
        if self.remote:
            try:
                endpoint = f"{self.url}/rest/v1/portfolio_state"
                payload = {"key": row_key, "content": data}
                r = requests.post(
                    endpoint,
                    params={"on_conflict": "key"},
                    headers=self._headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
                    json=payload,
                    timeout=20,
                )
                r.raise_for_status()
                self.last_error = None
                return True
            except requests.RequestException as exc:
                self.last_error = f"Supabase write failed: {exc}"
                return False

        file = ES_FILE if lang == "es" else EN_FILE
        file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True

    def upload_media(self, uploaded_file, prefix="evidence"):
        safe_name = Path(uploaded_file.name).name.replace(" ", "_")
        object_name = f"{prefix}/{uuid.uuid4().hex}_{safe_name}"
        content = uploaded_file.getvalue()
        mime = uploaded_file.type or "application/octet-stream"

        if self.remote:
            try:
                endpoint = f"{self.url}/storage/v1/object/{self.bucket}/{object_name}"
                headers = {
                    "apikey": self.key,
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": mime,
                    "x-upsert": "false",
                }
                r = requests.post(endpoint, headers=headers, data=content, timeout=90)
                r.raise_for_status()
                self.last_error = None
                return f"{self.url}/storage/v1/object/public/{self.bucket}/{object_name}"
            except requests.RequestException as exc:
                self.last_error = f"Supabase upload failed: {exc}"
                return None

        UPLOADS.mkdir(parents=True, exist_ok=True)
        path = UPLOADS / Path(object_name).name
        path.write_bytes(content)
        return str(path.relative_to(BASE)).replace("\\", "/")

    def bootstrap_remote(self):
        if not self.remote:
            return False
        ok = True
        for lang in ("es", "en"):
            current = self._local_load(lang)
            if not self.save(current, lang):
                ok = False
        return ok
