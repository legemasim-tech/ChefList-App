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
                st.error(f"❌ YouTube Blockade: {str(e)}")
                return None

        subs = info.get('subtitles') or info.get('automatic_captions')

        if not subs:
            st.error("❌ Keine Untertitel gefunden.")
            return None

        target_url = None
        for lang in ['de', 'de-orig', 'en', 'en-orig']:
            if lang in subs:
                for sub_format in subs[lang]:
                    if sub_format.get('ext') == 'json3':
                        target_url = sub_format.get('url')
                        break
                if target_url: break

        if not target_url:
            st.error("❌ Keine abrufbaren Untertitel gefunden.")
            return None

        res = requests.get(target_url)
        if 'json3' in target_url:
            data = res.json()
            text_fragments = [seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '').strip()]
            return " ".join(text_fragments)
        else:
            return " ".join(re.sub(r'<[^>]+>', ' ', res.text).split())

    except Exception as e:
        st.error(f"❌ Fehler: {str(e)}")
        return None

# --- KI FUNKTION ---
def generate_smart_list(text, tag):
    system_prompt = f"Erstelle eine Einkaufsliste als Markdown-Tabelle: Menge | Zutat | Kaufen (Link: https://www.amazon.de/s?k=[ZUTAT]&tag={tag})"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text[:15000]}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"KI-Fehler: {str(e)}")
        return None

# --- PDF GENERATOR (SCHÖN & OHNE LINKS) ---
def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 10, txt="ChefList Pro - Deine Einkaufsliste", ln=True, align='C')
    pdf.ln(10)
    
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or '---' in line: continue
        
        # Logik: Wenn es eine Tabellenzeile ist, nimm nur Menge und Zutat
        if '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                # Wir ignorieren alles nach der zweiten Spalte (die Links)
                menge = parts[0].replace('*', '')
                zutat = parts[1].replace('*', '')
                
                if "Menge" in menge or "Zutat" in zutat:
                    pdf.set_font("Arial", 'B', 12)
                    clean_line = f"{menge.ljust(15)} | {zutat}"
                else:
                    pdf.set_font("Arial", '', 12)
                    clean_line = f"[ ] {menge} {zutat}"
                
                safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 8, txt=safe_text)
        else:
            # Normaler Text ohne Links
            clean_line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line).replace('*', '')
            safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 8, txt=safe_text)

    return bytes(pdf.output())

# --- INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")
st.title("🍲 ChefList Pro")
video_url = st.text_input("YouTube Link:")

if st.button("Liste generieren"):
    if video_url:
        with st.status("Verarbeite..."):
            text = get_transcript(video_url)
            if text:
                result = generate_smart_list(text, amazon_tag)
                st.success("Erledigt!")
                st.markdown(result)
                pdf_bytes = create_pdf(result)
                st.download_button("📄 PDF herunterladen", data=pdf_bytes, file_name="Einkaufsliste.pdf", mime="application/pdf")
