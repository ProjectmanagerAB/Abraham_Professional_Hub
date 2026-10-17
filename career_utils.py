import json
from pathlib import Path

def load_career_history():
    path = Path(__file__).parent / 'career_history_2007_2018.json'
    return json.loads(path.read_text(encoding='utf-8')).get('experiences', [])
