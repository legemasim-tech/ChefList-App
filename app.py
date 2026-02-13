import streamlit as st
import openai
import requests
import re
import urllib.parse as urlparse
import yt_dlp
import json

# --- KONFIGURATION ---
api_key = st.secrets["OPENAI_API_KEY"]
amazon_tag = "markusapp-21" 

if not api_key:
    st.error("Bitte trage deinen OpenAI API Key ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- FUNKTION: VIDEO ID EXTRAHIEREN ---
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1][:11]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1][:11]
    elif "shorts/" in url:
        return url.split("shorts/")[1][:11]
    else:
        return None

# --- PLAN C: UNTERTITEL ÜBER YT-DLP (DER SMART-TV TRICK) ---
def get_transcript(video_url):
    """Extrahiert den rohen Untertitel-Link direkt aus den Video-Metadaten"""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("❌ Link-Format nicht erkannt.")
            return None

        # Konfiguration für yt-dlp (Wir laden kein Video, lesen nur Infos!)
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['de', 'en'],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Wir holen uns die Metadaten des Videos
            info = ydl.extract_info(video_url, download=False)

        # Wir prüfen, ob es manuell geschriebene oder automatisch generierte Untertitel gibt
        subs = info.get('subtitles', {})
        if not subs:
            subs = info.get('automatic_captions', {})

        if not subs:
            st.error("❌ Das Video hat absolut keine Untertitel (weder manuell noch automatisch).")
            return None

        # Wir suchen nach dem Direkt-Link für Deutsch ('de') oder Englisch ('en')
        target_url = None
        for lang in ['de', 'en']:
            if lang in subs:
                # Wir suchen bevorzugt das 'json3' Format, weil es am saubersten ist
                for sub_format in subs[lang]:
                    if sub_format.get('ext') == 'json3':
                        target_url = sub_format.get('url')
                        break
                # Fallback: Wenn kein json3 da ist, nehmen wir das erste verfügbare Format
                if not target_url and len(subs[lang]) > 0:
                    target_url = subs[lang][0].get('url')
                
                if target_url:
                    break

        if not target_url:
            st.error("❌ Keine deutschen oder englischen Untertitel gefunden.")
            return None

        # Wir laden die tatsächliche Untertitel-Datei über den extrahierten Direkt-Link herunter
        res = requests.get(target_url)
        
        # Wenn es das saubere JSON3 Format ist, extrahieren wir nur die Wörter
        if 'json3' in target_url:
            data = res.json()
            text_fragments = []
            for event in data.get('events', []):
                if 'segs' in event:
                    for seg in event['segs']:
                        text = seg.get('utf8', '')
                        if text.strip():
                            text_fragments.append(text)
            clean_text = " ".join(text_fragments)
            
        else:
            # Fallback für andere Formate (z.B. VTT) - Rohe Textbereinigung
            raw_text = res.text
            clean_text = re.sub(r'<[^>]+>', ' ', raw_text)
            clean_text = re.sub(r'\d{2}:\d{2}:\d{2}.*', '', clean_text)
            clean_text = " ".join(clean_text.split())

        return clean_text

    except Exception as e:
        st.error(f"❌ Fehler bei der Metadaten-Extraktion: {str(e)}")
        return None

# --- KI FUNKTION ---
def generate_smart_list(text, tag):
    system_prompt = f"""
    Du bist ein hilfreicher Koch-Assistent.
    
    DEINE AUFGABE:
    1. Analysiere das Transkript und extrahiere alle Zutaten.
    2. Suche explizit nach MENGENANGABEN.
    3. Erstelle eine Markdown-Tabelle mit 3 Spalten: "Menge", "Zutat", "Kaufen".
    
    WICHTIG - DER LINK:
    Das Format für den Link in der Spalte "Kaufen" ist: https://www.amazon.de/s?k=[ZUTAT]&tag={tag}
    Ersetze [ZUTAT] durch den exakten Namen. Der Link-Text ist "🛒 Auf Amazon suchen".
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        return response.choices
