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

# --- PDF GENERATOR (DER "TEXT-ONLY" FIX) ---
def create_pdf(text_content):
    """Nimmt nur die ersten beiden Spalten der Tabelle und druckt sie als simplen Text."""
    pdf = FPDF()
    pdf.add_page()
    # Wir nutzen Helvetica, das ist Standard und macht am wenigsten Probleme
    pdf.set_font("Helvetica", size=11)
    
    # Titel
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, txt="ChefList Pro - Deine Einkaufsliste", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", size=11)
    
    # Wir zerlegen den Text in Zeilen
    lines = text_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Trennlinien (---) ignorieren
        if '---' in line: continue
        
        clean_line = ""
        
        # Ist es eine Tabelle? (Erkennbar am senkrechten Strich |)
        if '|' in line:
            # Wir zerhacken die Zeile an den Strichen
            parts = line.split('|')
            # Leere Teile (ganz am Anfang/Ende) entfernen
            parts = [p.strip() for p in parts if p.strip()]
            
            # Wir nehmen NUR die ersten zwei Teile (Menge und Zutat)
            # Alles was danach kommt (Links, Emojis) ignorieren wir komplett!
            if len(parts) >= 2:
                menge = parts[0].replace('*', '') # Keine Sternchen
                zutat = parts[1].replace('*', '')
                
                # Wir bauen eine einfache Textzeile
                clean_line = f"[ ] {menge}: {zutat}"
                
                # Falls es die Überschrift ist, machen wir sie fett
                if "Menge" in menge and "Zutat" in zutat:
                    pdf.set_font("Helvetica", 'B', 11)
                    clean_line = "MENGE  -  ZUTAT"
                else:
                    pdf.set_font("Helvetica", '', 11)
        else:
            # Kein Tabellen-Strich? Dann ist es normaler Einleitungstext.
            # Aber wir löschen sicherheitshalber alle Links raus.
            clean_line = re.sub(r'\[.*?\]\(.*?\)', '', line)
            clean_line = clean_line.replace('*', '') # Keine Sternchen

        # FEUERFREI: Wir schreiben die Zeile ins PDF
        if clean_line:
            try:
                # Wir konvertieren den Text in "Latin-1".
                # Alle Zeichen, die das PDF nicht kennt (z.B. Emojis, kyrillisch),
                # werden durch 'replace' einfach durch ein Fragezeichen ersetzt.
                # So stürzt nichts mehr ab!
                safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 7, txt=safe_text, align='L')
            except:
                pass # Wenn eine Zeile immer noch bockt, ignorieren wir sie einfach

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
