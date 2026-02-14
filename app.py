import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF

# --- 1. KONFIGURATION & API ---
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = None

amazon_tag = "cheflist21-21" 

if not api_key:
    st.error("Bitte trage deinen OpenAI API Key in die Streamlit Secrets ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- 2. HILFSFUNKTIONEN ---
def get_video_data(video_url):
    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'writesubtitles': True, 'writeautomaticsub': True, 'subtitleslangs': ['de', 'en']}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        
        video_title = info.get('title', 'Rezept')
        subs = info.get('subtitles') or info.get('automatic_captions')
        
        if not subs: return video_title, None
        
        target_url = None
        for lang in ['de', 'de-orig', 'en', 'en-orig']:
            if lang in subs:
                for f in subs[lang]:
                    if f.get('ext') == 'json3':
                        target_url = f.get('url')
                        break
                if target_url: break
        
        transcript = None
        if target_url:
            res = requests.get(target_url)
            if 'json3' in target_url:
                data = res.json()
                transcript = " ".join([seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])
        
        return video_title, transcript
    except:
        return "Rezept", None

def generate_smart_list(text, tag):
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
def create_pdf(text_content, recipe_title):
    pdf = FPDF()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    
    display_title = recipe_title if len(recipe_title) <= 40 else recipe_title[:37] + "..."
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font("Arial", style="B", size=14)
    pdf_header = f"Einkaufsliste: {display_title}"
    try:
        safe_header = pdf_header.encode('latin-1', 'replace').decode('latin-1')
    except:
        safe_header = "Einkaufsliste"
        
    pdf.cell(190, 15, txt=safe_header, ln=True, align='C', fill=True)
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
                pdf.set_draw_color(220, 220, 220)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
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
st.set_page_config(page_title="ChefList Pro", page_icon="🍲", layout="centered")

if "recipe_result" not in st.session_state:
    st.session_state.recipe_result = None
if "recipe_title" not in st.session_state:
    st.session_state.recipe_title = ""

# --- SIDEBAR (NEU SORTIERT) ---
with st.sidebar:
    st.title("🍳 ChefList Pro")
    st.info("Dein smarter Küchenhelfer.")
    
    # Der Expander sitzt jetzt direkt unter der Info-Box
    with st.expander("ℹ️ Über & Rechtliches"):
        st.subheader("Was ist ChefList Pro?")
        st.write("Wandle Kochvideos in Sekunden in organisierte Einkaufslisten um.")
        
        st.divider()
        st.subheader("⚖️ Impressum")
        st.caption("**Betreiber:**\n\n[Dein Name]\n\n[Strasse]\n\n[PLZ Ort]")
        st.caption("**Kontakt:** [Deine E-Mail]")
        
        st.divider()
        st.subheader("✨ Affiliate Hinweis")
        st.caption("Als Amazon-Partner verdiene ich an qualifizierten Verkäufen. Die Links in der Tabelle (*) sind Affiliate-Links.")
        
        st.divider()
        st.subheader("🛡️ Datenschutz")
        st.caption("Wir speichern keine Video-URLs oder persönlichen Daten.")

# --- HAUPTBEREICH ---
st.title("🍲 Deine smarte Einkaufsliste")
st.write("YouTube-Link einfügen und Liste generieren!")

video_url = st.text_input("YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Jetzt Liste erstellen ✨", use_container_width=True):
    if video_url:
        with st.status("Verarbeite Video...", expanded=True) as status:
            title, text = get_video_data(video_url)
            st.session_state.recipe_title = title
            if text:
                result = generate_smart_list(text, amazon_tag)
                st.session_state.recipe_result = result
                status.update(label="Analyse abgeschlossen!", state="complete", expanded=False)
            else:
                st.error("Keine Untertitel gefunden.")

if st.session_state.recipe_result:
    st.divider()
    display_title_ui = st.session_state.recipe_title if len(st.session_state.recipe_title) <= 60 else st.session_state.recipe_title[:57] + "..."
    st.subheader(f"📋 Einkaufsliste für: {display_title_ui}")
    st.markdown(st.session_state.recipe_result)
    
    st.divider()
    col1, col2 = st.columns([2,1])
    with col1:
        st.write("Fertig zum Einkaufen? Lade dir die Liste als PDF herunter:")
    with col2:
        try:
            pdf_data = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title)
            short_title = st.session_state.recipe_title[:40].strip()
            clean_filename = re.sub(r'[^\w\s-]', '', short_title).strip().replace(' ', '_')
            
            st.download_button(
                label="📄 PDF Download",
                data=pdf_data,
                file_name=f"Einkaufsliste_{clean_filename}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error("Fehler beim PDF-Erzeugen.")
