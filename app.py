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
    system_prompt = f"Du bist ein hilfreicher Koch-Assistent. Erstelle eine saubere Markdown-Tabelle: Menge | Zutat | Kaufen (Link: https://www.amazon.de/s?k=[ZUTAT]&tag={tag})"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text[:15000]}]
        )
        return response.choices[0].message.content
    except: return None

# --- 3. PDF GENERATOR (SCHÖN & STABIL) ---
def create_pdf(text_content):
    pdf = FPDF()
    pdf.set_margins(left=15, top=15, right=15)
    pdf.add_page()
    
    # Header Design
    pdf.set_fill_color(245, 245, 245) 
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(0, 15, txt="MEINE EINKAUFSLISTE", ln=True, align='C', fill=True)
    pdf.ln(10)
    
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line or '---' in line: continue
        
        # Link-Bereinigung: Alles in Klammern (http...) löschen
        clean_line = re.sub(r'\(http[^\)]+\)', '', line)
        clean_line = clean_line.replace('*', '').replace('[', '').replace(']', '')

        # Tabellen-Zeilen erkennen
        if '|' in line:
            parts = [p.strip() for p in clean_line.split('|') if p.strip()]
            if len(parts) >= 2:
                menge = parts[0]
                zutat = parts[1]
                
                if "Menge" in menge and "Zutat" in zutat:
                    pdf.set_font("Arial", style="B", size=11)
                    display_text = "MENGE  -  ZUTAT"
                else:
                    pdf.set_font("Arial", size=12)
                    display_text = f"[  ] {menge} {zutat}"
                
                try:
                    safe_text = display_text.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 10, txt=safe_text, align='L')
                    # Dezente Trennlinie
                    pdf.set_draw_color(220, 220, 220)
                    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                    pdf.ln(1)
                except: continue
        else:
            # Normaler Text (Einleitung)
            pdf.set_font("Arial", style="I", size=10)
            try:
                safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 7, txt=safe_text, align='L')
            except: continue

    return bytes(pdf.output())

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")

# Gedächtnis-Initialisierung
if "recipe_result" not in st.session_state:
    st.session_state.recipe_result = None

st.title("🍲 ChefList Pro")
st.write("Deine Einkaufsliste direkt aus dem YouTube-Video.")

video_url = st.text_input("YouTube Link:", placeholder="https://youtube.com/...")

# Generieren
if st.button("Liste generieren 💸"):
    if video_url:
        with st.status("Rezept wird analysiert...", expanded=True) as status:
            text = get_transcript(video_url)
            if text:
                result = generate_smart_list(text, amazon_tag)
                st.session_state.recipe_result = result
                status.update(label="Fertig!", state="complete", expanded=False)
            else:
                st.error("Keine Untertitel gefunden.")

# Anzeige & Download
if st.session_state.recipe_result:
    st.success("Hier ist deine Liste:")
    st.markdown("---")
    # In der App-Ansicht lassen wir die volle Tabelle mit Links stehen
    st.markdown(st.session_state.recipe_result)
    
    st.markdown("---")
    st.write("💾 **PDF für den Supermarkt:**")
    
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
