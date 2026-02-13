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
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 10, txt="ChefList Pro - Deine Einkaufsliste", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=11)
    
    # Wir nehmen den Text fast 1:1, putzen aber nur die Links extrem simpel
    lines = text_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or '---' in line: continue
        
        # 1. Wir entfernen nur die URL in den Klammern: [Text](URL) -> Text
        # Das ist viel sicherer als nach http zu suchen
        clean_line = re.sub(r'\(http[^\)]+\)', '', line)
        
        # 2. Wir entfernen die eckigen Klammern, Sterne und Tabellenstriche
        clean_line = clean_line.replace('[', '').replace(']', '').replace('*', '').replace('|', '  ')
        
        # 3. WICHTIG: Wir begrenzen die Zeilenlänge manuell, damit FPDF nicht rechnet
        if len(clean_line) > 90:
            clean_line = clean_line[:87] + "..."

        try:
            # Latin-1 ist Pflicht für FPDF
            safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 8, txt=safe_text, ln=True) # cell statt multi_cell ist hier stabiler
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
