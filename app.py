import streamlit as st
import openai
import requests
import re
import urllib.parse as urlparse
import yt_dlp
import json
from fpdf import FPDF
import unicodedata # <--- NEU: Hilft gegen seltsame Zeichen

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
            st.error("❌ Das Video hat absolut keine Untertitel (weder manuell noch automatisch).")
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

# --- PDF GENERATOR (ROBUST & SAUBER) ---
def create_pdf(text_content):
    """Konvertiert die Markdown-Tabelle in ein sauberes PDF"""
    pdf = FPDF()
    pdf.add_page()
    
    # Titel hinzufügen
    pdf.set_font("helvetica", style="B", size=16)
    pdf.cell(0, 10, txt="ChefList Pro - Deine Einkaufsliste", ln=True, align='C')
    pdf.ln(5)
    
    # 1. Text bereinigen (Links entfernen)
    # Entfernt [Text](URL) und behält nur Text
    text_content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text_content)
    
    # 2. Markdown-Fettgedrucktes entfernen (**Wort** -> Wort)
    text_content = text_content.replace("**", "")
    
    # 3. Unicode Normalisierung (Verwandelt "é" in "e" und entfernt unlesbare Zeichen)
    # Das ist der WICHTIGSTE Schritt, damit der Text nicht verschwindet!
    text_content = unicodedata.normalize('NFKD', text_content).encode('ascii', 'ignore').decode('ascii')
    
    pdf.set_font("courier", size=10) # Courier ist gut für Tabellen/Listen
    
    lines = text_content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Leere Zeilen überspringen
        if not line:
            continue
            
        # Tabellen-Trennlinien (---|---|---) überspringen
        if '---' in line and '|' in line:
            continue
            
        # Wenn es eine Tabellenzeile ist (enthält |), schön formatieren
        if '|' in line:
            # Teile die Zeile an den Strichen
            parts = [p.strip() for p in line.split('|') if p.strip()]
            
            # Wenn wir 3 Teile haben (Menge, Zutat, Link-Text), formatieren wir es als Liste
            if len(parts) >= 2:
                # Wir bauen einen schönen String: "[ ] Menge - Zutat"
                # Wir ignorieren die Spalte "Kaufen", da Links im Papier-PDF sinnlos sind
                formatted_line = f"[ ] {parts[0]} - {parts[1]}"
                pdf.multi_cell(0, 6, txt=formatted_line, align='L')
            else:
                # Falls Struktur unklar, drucke die Zeile einfach ohne Striche
                clean_line = line.replace('|', ' ').strip()
                pdf.multi_cell(0, 6, txt=clean_line, align='L')
                
        else:
            # Ganz normaler Text (z.B. die Einleitung)
            pdf.multi_cell(0, 6, txt=line, align='L')
            
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
                    
                    # PDF erzeugen
                    pdf_bytes = create_pdf(result)
                    
                    # Download-Button
                    st.download_button(
                        label="📄 Als PDF herunterladen",
                        data=pdf_bytes,
                        file_name="ChefList_Einkaufsliste.pdf",
                        mime="application/pdf"
                    )
                    
                else:
                    status.update(label="KI Fehler", state="error")
            else:
                status.update(label="Keine Untertitel gefunden", state="error")


