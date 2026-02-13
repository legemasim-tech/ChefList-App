import streamlit as st
import openai
import requests
import re
import urllib.parse as urlparse
import yt_dlp
import json
from fpdf import FPDF

# --- 1. KONFIGURATION & API ---
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = None

amazon_tag = "markusapp-21" 

if not api_key:
    st.error("Bitte trage deinen OpenAI API Key in die Streamlit Secrets ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- 2. HILFSFUNKTIONEN ---
def extract_video_id(url):
    """Extrahiert die 11-stellige Video-ID aus verschiedenen YouTube-Formaten."""
    if "v=" in url:
        return url.split("v=")[1][:11]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1][:11]
    elif "shorts/" in url:
        return url.split("shorts/")[1][:11]
    return None

def get_transcript(video_url):
    """Holt Untertitel via yt-dlp (Smart-TV Trick)."""
    try:
        ydl_opts = {
            'quiet': True, 
            'skip_download': True, 
            'writesubtitles': True, 
            'writeautomaticsub': True, 
            'subtitleslangs': ['de', 'en']
        }
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
    except:
        return None

def generate_smart_list(text, tag):
    """KI erstellt die Einkaufsliste aus dem Transkript."""
    system_prompt = f"""
    Du bist ein Koch-Assistent. Erstelle eine Markdown-Tabelle: 
    Menge | Zutat | Kaufen (Link: https://www.amazon.de/s?k=[ZUTAT]&tag={tag})
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text[:15000]}]
        )
        return response.choices[0].message.content
    except:
        return None

# --- 3. PDF GENERATOR ---
def create_pdf(text_content):
    """Erstellt ein PDF, das garantiert linksbündig bleibt und nicht abstürzt."""
    pdf = FPDF()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(190, 15, txt="MEINE EINKAUFSLISTE", ln=True, align='C', fill=True)
    pdf.ln(8)
    
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or '---' in line: continue
        
        pdf.set_x(10) # Stift immer nach links setzen
        
        if '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                # Überschrift oder Zutat?
                if "Menge" in parts[0] or "Zutat" in parts[1]:
                    pdf.set_font("Arial", style="B", size=11)
                    clean_line = "MENGE - ZUTAT"
                else:
                    pdf.set_font("Arial", size=12)
                    m = parts[0].replace('*', '')
                    z = parts[1].replace('*', '')
                    clean_line = f"[  ] {m} {z}"
                
                try:
                    safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(190, 10, txt=safe_text, ln=True, align='L')
                    # Trennlinie
                    pdf.set_draw_color(220, 220, 220)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(1)
                except: continue
        else:
            # Normaler Text (Einleitung etc.)
            clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line).replace('*', '')
            pdf.set_font("Arial", style="I", size=10)
            try:
                safe_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(190, 7, txt=safe_text, align='L')
            except: continue

    return bytes(pdf.output())

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")

# Session State Gedächtnis
if "recipe_result" not in st.session_state:
    st.session_state.recipe_result = None

st.title("🍲 ChefList Pro")
st.write("Wandle jedes Kochvideo in eine smarte Einkaufsliste um.")

video_url = st.text_input("YouTube Link einfügen:", placeholder="https://youtube.com/...")

# Generieren Button
if st.button("Liste generieren 💸"):
    if not video_url:
        st.warning("Bitte gib zuerst einen Link ein.")
    else:
        with st.status("Rezept wird analysiert...", expanded=True) as status:
            st.write("1. Suche Untertitel...")
            text = get_transcript(video_url)
            if text:
                st.write("2. KI erstellt Liste...")
                result = generate_smart_list(text, amazon_tag)
                st.session_state.recipe_result = result
                status.update(label="Fertig!", state="complete", expanded=False)
            else:
                st.error("Konnte keine Untertitel finden.")

# Anzeige & Download (wenn Ergebnis vorhanden)
if st.session_state.recipe_result:
    st.success("Hier ist deine Liste:")
    st.markdown("---")
    st.markdown(st.session_state.recipe_result)
    
    st.markdown("---")
    st.write("💾 **PDF-Export für den Einkauf:**")
    
    try:
        pdf_data = create_pdf(st.session_state.recipe_result)
        st.download_button(
            label="📄 PDF herunterladen",
            data=pdf_data,
            file_name="Einkaufsliste.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Fehler beim PDF-Export: {str(e)}")
