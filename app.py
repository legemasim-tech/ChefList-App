import streamlit as st
import openai
import requests
import re
import urllib.parse as urlparse
import yt_dlp
import json

# --- KONFIGURATION ---
# Versuche den API-Key sicher zu laden
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = None

amazon_tag = "markusapp-21" 

if not api_key:
    st.error("Bitte trage deinen OpenAI API Key in die Streamlit Secrets ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- FUNKTION: VIDEO ID EXTRAHIEREN ---
def extract_video_id(url):
    if "v=" in url:
        try:
            return url.split("v=")[1][:11]
        except:
            return None
    elif "youtu.be/" in url:
        try:
            return url.split("youtu.be/")[1][:11]
        except:
            return None
    elif "shorts/" in url:
        try:
            return url.split("shorts/")[1][:11]
        except:
            return None
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
            'writesubtitles': True, # Wir wollen Untertitel
            'writeautomaticsub': True, # Auch automatische
            'subtitleslangs': ['de', 'en'], # Deutsch und Englisch
            'cookiefile': None # Keine Cookies nutzen
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Wir holen uns die Metadaten des Videos
            try:
                info = ydl.extract_info(video_url, download=False)
            except Exception as e:
                st.error(f"❌ YouTube Blockade oder Video nicht verfügbar: {str(e)}")
                return None

        # Wir prüfen, ob es manuell geschriebene oder automatisch generierte Untertitel gibt
        subs = info.get('subtitles')
        if not subs:
            subs = info.get('automatic_captions')

        if not subs:
            st.error("❌ Das Video hat absolut keine Untertitel (weder manuell noch automatisch).")
            return None

        # Wir suchen nach dem Direkt-Link für Deutsch ('de') oder Englisch ('en')
        target_url = None
        
        # Liste der Sprachen, die wir akzeptieren (bevorzugt Deutsch)
        langs_to_check = ['de', 'de-orig', 'en', 'en-orig']
        
        for lang in langs_to_check:
            if lang in subs:
                # Wir suchen bevorzugt das 'json3' Format
                for sub_format in subs[lang]:
                    if sub_format.get('ext') == 'json3':
                        target_url = sub_format.get('url')
                        break
                # Fallback: Wenn kein json3 da ist, erstes Format nehmen
                if not target_url and len(subs[lang]) > 0:
                    target_url = subs[lang][0].get('url')
                
                if target_url:
                    break

        if not target_url:
            # Letzter Versuch: Irgendeine Sprache nehmen, falls vorhanden
            first_lang = list(subs.keys())[0]
            if subs[first_lang]:
                target_url = subs[first_lang][0].get('url')

        if not target_url:
            st.error("❌ Keine abrufbaren Untertitel gefunden.")
            return None

        # Wir laden die tatsächliche Untertitel-Datei herunter
        res = requests.get(target_url)
        
        # JSON3 Verarbeitung (Sauberste Methode)
        if 'json3' in target_url:
            try:
                data = res.json()
                text_fragments = []
                for event in data.get('events', []):
                    if 'segs' in event:
                        for seg in event['segs']:
                            text = seg.get('utf8', '')
                            # Filtere Zeitstempel und leere Zeilen
                            if text and text.strip() and not text.startswith('\n'):
                                text_fragments.append(text.strip())
                clean_text = " ".join(text_fragments)
            except:
                clean_text = res.text # Fallback
        else:
            # Fallback für andere Formate (z.B. VTT/XML)
            raw_text = res.text
            # HTML Tags entfernen
            clean_text = re.sub(r'<[^>]+>', ' ', raw_text)
            # Zeitstempel entfernen (grobe Reinigung)
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
    Ersetze [ZUTAT] durch den exakten Namen der Zutat (URL-Codiert). 
    Der Link-Text ist "🛒 Auf Amazon suchen".
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text[:15000]} # Limitierung auf 15k Zeichen
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"KI-Fehler: {str(e)}")
        return None

# --- INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")

st.title("🍲 ChefList Pro (Turbo Version ⚡)")
st.write("Füge einen YouTube-Link ein. Ich lese das Rezept ohne Proxys direkt aus!")

video_url = st.text_input("YouTube Link:", placeholder="https://youtube.com/...")

if st.button("Liste generieren 💸"):
    if not video_url:
        st.warning("Bitte erst einen Link eingeben!")
    else:
        with st.status("Analysiere Rezept...", expanded=True) as status:
            
            st.write("1. Lese Video-Daten (Smart-TV Modus)... 📺")
            text = get_transcript(video_url)
            
            if text:
                st.write(f"✅ Transkript gefunden ({len(text)} Zeichen)!")
                st.write("2. KI schreibt Einkaufsliste... 🧠")
                result = generate_smart_list(text, amazon_tag)
                
                if result:
                    status.update(label="Fertig!", state="complete", expanded=False)
                    
                    st.success("Hier ist deine smarte Liste:")
                    st.markdown("---")
                    st.markdown(result)
                else:
                    status.update(label="KI Fehler", state="error")
            else:
                status.update(label="Keine Untertitel gefunden", state="error")
