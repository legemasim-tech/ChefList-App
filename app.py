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
        return url.split("v=")[1][:11]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1][:11]
    elif "shorts/" in url:
        return url.split("shorts/")[1][:11]
    return None

# --- UNTERTITEL ÜBER YT-DLP ---
def get_transcript(video_url):
    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'writesubtitles': True, 'writeautomaticsub': True, 'subtitleslangs': ['de', 'en']}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        subs = info.get('subtitles') or info.get('automatic_captions')
        if not subs: return None
        target_url = None
        for lang in ['de', 'de-orig', 'en', 'en-orig']:
            if lang in subs:
                for f in subs[lang]:
                    if f.get('ext') == 'json3':
                        target_url = f.get('url')
                        break
                if target_url: break
        if not target_url: return None
        res = requests.get(target_url)
        if 'json3' in target_url:
            data = res.json()
            return " ".join([seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])
        return " ".join(re.sub(r'<[^>]+>', ' ', res.text).split())
    except: return None

# --- KI FUNKTION ---
def generate_smart_list(text, tag):
    system_prompt = f"Du bist ein Koch-Assistent. Erstelle eine Tabelle: Menge | Zutat | Kaufen (Link: https://www.amazon.de/s?k=[ZUTAT]&tag={tag})"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text[:15000]}]
        )
        return response.choices[0].message.content
    except: return None

# --- PDF GENERATOR (DER "SIMPEL-FIX") ---
def create_pdf(text_content):
    """Erstellt ein schön formatiertes PDF, das garantiert linksbündig bleibt."""
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Kopfzeile
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 15, txt="MEINE EINKAUFSLISTE", ln=True, align='C', fill=True)
    pdf.ln(8)
    
    # 2. Inhalt verarbeiten
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        
        # Unnötiges filtern (Trennstriche und leere Zeilen)
        if not line or '---' in line:
            continue
        
        # Tabellenlogik: Menge | Zutat | Link
        if '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            
            # Wir prüfen, ob es die Kopfzeile der Tabelle ist
            if len(parts) >= 2 and ("Menge" in parts[0] or "Zutat" in parts[1]):
                pdf.set_font("Arial", style="B", size=11)
                menge_zutat = f"MENGE - ZUTAT"
            elif len(parts) >= 2:
                pdf.set_font("Arial", size=12)
                # Wir nehmen nur Menge (parts[0]) und Zutat (parts[1])
                menge = parts[0].replace('*', '')
                zutat = parts[1].replace('*', '')
                menge_zutat = f"[  ] {menge} {zutat}"
            else:
                continue

            try:
                # Wir nutzen hier eine feste Breite von 0 (bis zum rechten Rand) 
                # und align='L' für Linksbuendig
                safe_text = menge_zutat.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 10, txt=safe_text, ln=True, align='L')
                
                # Dezente Trennlinie
                current_y = pdf.get_y()
                pdf.set_draw_color(220, 220, 220)
                pdf.line(10, current_y, 200, current_y)
                pdf.ln(1)
            except:
                continue
        else:
            # Für normalen Text (Einleitung/Abschluss)
            # Links entfernen
            clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line).replace('*', '')
            pdf.set_font("Arial", style="I", size=10)
            try:
                safe_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 7, txt=safe_text, align='L')
            except:
                continue

    return bytes(pdf.output())

# --- INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")
st.title("🍲 ChefList Pro")
st.write("Link einfügen und Einkaufsliste erhalten!")

video_url = st.text_input("YouTube Link:")

if st.button("Liste generieren"):
    if video_url:
        with st.spinner("Rezept wird gelesen..."):
            text = get_transcript(video_url)
            if text:
                result = generate_smart_list(text, amazon_tag)
                if result:
                    st.success("Hier ist deine Liste:")
                    st.markdown(result)
                    
                    # PDF Download
                    try:
                        pdf_data = create_pdf(result)
                        st.download_button(
                            label="📄 PDF herunterladen",
                            data=pdf_data,
                            file_name="Einkaufsliste.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"PDF-Fehler: {str(e)}")
                else:
                    st.error("KI konnte keine Liste erstellen.")
            else:
                st.error("Keine Untertitel gefunden.")


