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

# Dein Amazon Partner-Tag
amazon_tag = "markusapp-21" 

if not api_key:
    st.error("Bitte trage deinen OpenAI API Key in die Streamlit Secrets ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- 2. HILFSFUNKTIONEN ---
def extract_video_id(url):
    if "v=" in url: return url.split("v=")[1][:11]
    elif "youtu.be/" in url: return url.split("youtu.be/")[1][:11]
    elif "shorts/" in url: return url.split("shorts/")[1][:11]
    return None

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

def generate_smart_list(text, tag):
    # Wir sagen der KI, dass sie ein Sternchen * für den rechtlichen Hinweis anhängen soll
    system_prompt = f"""
    Du bist ein Koch-Assistent. Erstelle eine Tabelle: Menge | Zutat | Kaufen.
    Der Link in der Spalte 'Kaufen' muss so aussehen: https://www.amazon.de/s?k=[ZUTAT]&tag={tag}
    Der Link-Text soll immer '🛒 Auf Amazon prüfen*' lauten.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text[:15000]}]
        )
        return response.choices[0].message.content
    except: return None

# --- 3. PDF GENERATOR ---
def create_pdf(text_content):
    pdf = FPDF()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(190, 15, txt="MEINE EINKAUFSLISTE", ln=True, align='C', fill=True)
    pdf.ln(8)
    
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or '---' in line: continue
        
        pdf.set_x(10)
        
        if '|' in line:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2 and ("Menge" in parts[0] or "Zutat" in parts[1]):
                pdf.set_font("Arial", style="B", size=11)
                menge_zutat = "MENGE - ZUTAT"
            elif len(parts) >= 2:
                pdf.set_font("Arial", size=12)
                m = parts[0].replace('*', '')
                z = parts[1].replace('*', '')
                menge_zutat = f"[  ] {m} {z}"
            else: continue

            try:
                safe_text = menge_zutat.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(190, 10, txt=safe_text, ln=True, align='L')
                current_y = pdf.get_y()
                pdf.set_draw_color(220, 220, 220)
                pdf.line(10, current_y, 200, current_y)
                pdf.ln(1)
            except: continue
        else:
            clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line).replace('*', '')
            pdf.set_font("Arial", style="I", size=10)
            try:
                safe_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(190, 7, txt=safe_text, align='L')
            except: continue

    return bytes(pdf.output())

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")

if "recipe_result" not in st.session_state:
    st.session_state.recipe_result = None

st.title("🍲 ChefList Pro")
st.write("Wandle Kochvideos in Einkaufslisten um und verdiene Provisionen.")

video_url = st.text_input("YouTube Link:")

if st.button("Liste generieren"):
    if video_url:
        with st.spinner("Rezept wird gelesen..."):
            text = get_transcript(video_url)
            if text:
                result = generate_smart_list(text, amazon_tag)
                st.session_state.recipe_result = result
            else:
                st.error("Keine Untertitel gefunden.")

if st.session_state.recipe_result:
    st.success("Hier ist deine Liste:")
    st.markdown(st.session_state.recipe_result)
    
    try:
        pdf_data = create_pdf(st.session_state.recipe_result)
        st.download_button(
            label="📄 PDF herunterladen",
            data=pdf_data,
            file_name="Einkaufsliste.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"PDF-Fehler: {str(e)}")

# --- 5. RECHTLICHER HINWEIS (AMAZON RICHTLINIE) ---
st.markdown("---")
st.caption("* Als Amazon-Partner verdiene ich an qualifizierten Verkäufen. Die Links in der Tabelle sind Affiliate-Links.")
