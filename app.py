import streamlit as st
import openai
import requests
import re
import urllib.parse as urlparse
import yt_dlp
import json
from fpdf import FPDF

# --- KONFIGURATION ---
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

# --- UNTERTITEL ÜBER YT-DLP (SMART-TV TRICK) ---
def get_transcript(video_url):
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("❌ Link-Format nicht erkannt.")
            return None

        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'writesubtitles': True, 
            'writeautomaticsub': True, 
            'subtitleslangs': ['de', 'en'], 
            'cookiefile': None 
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=False)
            except Exception as e:
                st.error(f"❌ YouTube Blockade oder Video nicht verfügbar: {str(e)}")
                return None

        subs = info.get('subtitles')
        if not subs:
            subs = info.get('automatic_captions')

        if not subs:
            st.error("❌ Das Video hat absolut keine Untertitel.")
            return None

        target_url = None
        langs_to_check = ['de', 'de-orig', 'en', 'en-orig']
        
        for lang in langs_to_check:
            if lang in subs:
                for sub_format in subs[lang]:
                    if sub_format.get('ext') == 'json3':
                        target_url = sub_format.get('url')
                        break
                if not target_url and len(subs[lang]) > 0:
                    target_url = subs[lang][0].get('url')
                if target_url:
                    break

        if not target_url:
            first_lang = list(subs.keys())[0]
            if subs[first_lang]:
                target_url = subs[first_lang][0].get('url')

        if not target_url:
            st.error("❌ Keine abrufbaren Untertitel gefunden.")
            return None

        res = requests.get(target_url)
        
        if 'json3' in target_url:
            try:
                data = res.json()
                text_fragments = []
                for event in data.get('events', []):
                    if 'segs' in event:
                        for seg in event['segs']:
                            text = seg.get('utf8', '')
                            if text and text.strip() and not text.startswith('\n'):
                                text_fragments.append(text.strip())
                clean_text = " ".join(text_fragments)
            except:
                clean_text = res.text 
        else:
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
    Ersetze [ZUTAT] durch den exakten Namen der Zutat (URL-Codiert). 
    Der Link-Text ist "🛒 Auf Amazon suchen".
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text[:15000]} 
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"KI-Fehler: {str(e)}")
        return None

# --- PDF GENERATOR (SIMPEL & SICHER) ---
def create_pdf(text_content):
    """Konvertiert die Markdown-Tabelle in ein einfaches, lesbares PDF"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10) # Standard Schriftart
    
    # Titel
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(0, 10, txt="ChefList Pro - Deine Einkaufsliste", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    
    # Wir gehen den Text Zeile für Zeile durch
    lines = text_content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # 1. Störende Markdown-Zeichen entfernen
        if '---' in line: continue # Trennlinien weg
        
        # 2. Links entfernen (Radikal: Alles ab 'http' oder '[Link' wegwerfen)
        # Wir wollen nur Menge und Zutat
        clean_line = line
        
        # Falls es eine Tabelle ist (mit Strichen |)
        if '|' in line:
            parts = line.split('|')
            # Leere Teile entfernen
            parts = [p.strip() for p in parts if p.strip()]
            
            # Wenn wir Menge und Zutat haben (mindestens 2 Teile)
            if len(parts) >= 2:
                col1 = parts[0].replace('*', '') # Menge
                col2 = parts[1].replace('*', '') # Zutat
                
                # Wir schreiben es einfach als Text: "Menge: Zutat"
                clean_line = f"[ ] {col1} - {col2}"
                
                # Wenn es die Überschrift ist
                if "Menge" in col1 and "Zutat" in col2:
                     pdf.set_font("Arial", 'B', 11)
                     clean_line = "MENGE   -   ZUTAT"
                else:
                     pdf.set_font("Arial", '', 11)

        # 3. Sicherheits-Encoding (Latin-1)
        # Ersetzt alle Zeichen, die das PDF nicht kennt, durch ein Fragezeichen
        try:
            safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 7, txt=safe_text, align='L')
        except:
            continue # Sollte dank 'replace' nicht passieren

    return bytes(pdf.output())

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
                    
                    st.markdown("---")
                    st.write("💾 **Speichere deine Liste für später:**")
                    
                    try:
                        pdf_bytes = create_pdf(result)
                        st.download_button(
                            label="📄 Als PDF herunterladen",
                            data=pdf_bytes,
                            file_name="ChefList_Einkaufsliste.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"PDF Fehler: {str(e)}")
                    
                else:
                    status.update(label="KI Fehler", state="error")
            else:
                status.update(label="Keine Untertitel gefunden", state="error")
