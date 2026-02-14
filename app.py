import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. KONFIGURATION & API ---
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = None

amazon_tag = "cheflist21-21" 
paypal_email = "legemasim@gmail.com"

pay_link_90c = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Rezept_Erstellung&amount=0.90&currency_code=EUR"

if not api_key:
    st.error("Bitte trage deinen OpenAI API Key in die Streamlit Secrets ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- 2. HILFSFUNKTIONEN ---
def get_full_video_data(video_url):
    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'writesubtitles': True, 'writeautomaticsub': True, 'subtitleslangs': ['de', 'en']}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        video_title = info.get('title', 'Rezept')
        description = info.get('description', '') 
        subs = info.get('subtitles') or info.get('automatic_captions')
        transcript = ""
        if subs:
            target_url = None
            for lang in ['de', 'de-orig', 'en', 'en-orig']:
                if lang in subs:
                    for f in subs[lang]:
                        if f.get('ext') == 'json3':
                            target_url = f.get('url')
                            break
                    if target_url: break
            if target_url:
                res = requests.get(target_url)
                if 'json3' in target_url:
                    data = res.json()
                    transcript = " ".join([seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])
        return video_title, transcript, description
    except:
        return "Rezept", None, None

def generate_smart_recipe(transcript, description, tag, portions, unit_system):
    combined_input = f"VIDEOTITEL:\n{transcript}\n\nINFOTEXT/BESCHREIBUNG:\n{description}"
    
    if unit_system == "US-Einheiten (cups/oz)":
        unit_instruction = "US-Einheiten (cups, oz, lbs, tsp, tbsp). Schreibe IMMER die Einheit (z.B. 'cups' oder 'oz') hinter die Menge!"
    else:
        unit_instruction = "METRISCH (g, ml, kg, l)."

    system_prompt = f"""
    Du bist ein Profi-Koch und Mathe-Experte. Erstelle das Rezept exakt für {portions} Person(en). 
    WICHTIG: Nutze das System {unit_instruction}.
    
    STRUKTUR:
    1. Eckdaten (Dauer, Schwierigkeit, Personenanzahl: {portions})
    2. Mengen-Tabelle (Menge | Zutat | Kaufen)
       -> Link: https://www.amazon.de/s?k=[ZUTAT]&tag={tag}
       -> Text: '🛒 Auf Amazon prüfen*'
    3. Zubereitung (Schritt-für-Schritt)
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input[:16000]}]
        )
        return response.choices[0].message.content
    except: return None

# --- 3. PDF GENERATOR ---
def clean_txt(text):
    if not text: return ""
    rep = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'Euro'}
    for k, v in rep.items():
        text = text.replace(k, v)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()

def create_pdf(text_content, recipe_title):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Logo bleibt hier draußen, um Abstürze zu vermeiden
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 12, clean_txt(f"Rezept: {recipe_title[:45]}"), ln=True, align='C', fill=True)
        pdf.ln(5)
        
        pdf.set_font("Arial", '', 10)
        is_step = False
        
        for line in text_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('---'): continue
            l_clean = clean_txt(line)
            
            if 'zubereitung' in l_clean.lower():
                is_step = True
                pdf.ln(5); pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 8, "ZUBEREITUNG:", ln=True); pdf.set_font("Arial", '', 10)
                continue

            if any(l_clean.startswith(h) for h in ['Dauer:', 'Schwierigkeit:', 'Backtemperatur:', 'Personen:']):
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, l_clean, ln=True); pdf.set_font("Arial", '', 10)
                continue

            if '|' in l_clean and not is_step:
                p = [i.strip() for i in l_clean.split('|') if i.strip()]
                if len(p) >= 2 and "zutat" not in p[1].lower():
                    pdf.cell(0, 6, f"- {p[0]} {p[1]}", ln=True)
            else:
                l_clean = l_clean.replace('**', '').replace('*', '')
                pdf.multi_cell(0, 6, l_clean)
                if is_step: pdf.ln(1)

        pdf.ln(10)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, "Guten Appetit wuenscht das Team von ChefList Pro!", align='C', ln=True)
        return pdf.output(dest='S').encode('latin-1')
    except: 
        return None

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")

# Logo in Sidebar mit CSS-Trick für Optik
st.markdown("""
    <style>
        [data-testid="stSidebar"] img {
            background-color: white;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.title("🍳 ChefList Pro")
    
    st.info(f"Analysen: {st.session_state.counter}")
    st.markdown(f'''<a href="{pay_link_90c}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold;">⚡ Projekt unterstützen (0,90€)</button></a>''', unsafe_allow_html=True)
    st.markdown("---")
    with st.expander("ℹ️ Über & Rechtliches"):
        st.caption("**Betreiber:** Markus Simmel")
        st.caption("**Kontakt:** legemasim@gmail.com")
        st.divider()
        st.caption("✨ Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.")
        st.divider()
        st.subheader("🛡️ Datenschutz")
        st.caption("Keine Datenspeicherung. Verarbeitung erfolgt verschlüsselt.")

st.title("🍲 ChefList Pro")

video_url = st.text_input("YouTube Link:", placeholder="Link einfügen...")
c1, c2 = st.columns(2)
portions = c1.slider("Portionen:", 1, 10, 4)
unit_system = c2.radio("System:", ["Metrisch (g/ml)", "US-Einheiten (cups/oz)"], horizontal=True)

if st.button("Rezept jetzt erstellen ✨", use_container_width=True):
    if video_url:
        with st.status("Analysiere Video...", expanded=True) as status:
            t, trans, d = get_full_video_data(video_url)
            st.session_state.recipe_title = t
            res = generate_smart_recipe(trans, d, amazon_tag, portions, unit_system)
            if res:
                st.session_state.recipe_result = res
                st.session_state.counter += 1
                status.update(label="Rezept bereit!", state="complete", expanded=False)
            else: st.error("Fehler bei der KI-Analyse.")

if st.session_state.recipe_result:
    st.divider()
    st.subheader(f"📖 {st.session_state.recipe_title}")
    st.markdown(st.session_state.recipe_result)
    
    st.divider()
    pdf_bytes = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title)
    if pdf_bytes:
        st.download_button("📄 PDF herunterladen", pdf_bytes, file_name="ChefList_Rezept.pdf", mime="application/pdf", use_container_width=True)
