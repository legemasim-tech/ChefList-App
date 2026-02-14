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
    
    unit_instruction = "US-Einheiten (cups, oz, lbs, tsp, tbsp)" if unit_system == "US-Einheiten (cups/oz)" else "METRISCH (g, ml, kg, l)"

    system_prompt = f"""
    Du bist ein Profi-Koch und Mathe-Experte. 
    WICHTIGSTE AUFGABE: Analysiere die Mengen im Video (oft für 2 oder 4 Personen) und RECHNE SIE MATHEMATISCH EXAKT auf genau {portions} Person(en) um.
    Die Mengen in der Tabelle MÜSSEN sich ändern, wenn die Personenanzahl {portions} geändert wird!
    
    NUTZE: {unit_instruction}. Schreibe bei US-Einheiten immer die Einheit hinter die Zahl.
    
    STRUKTUR:
    1. Eckdaten (Dauer, Schwierigkeit, Personenanzahl: {portions})
    2. Mengen-Tabelle (Menge | Zutat | Kaufen)
       -> Link: https://www.amazon.de/s?k=[ZUTAT]&tag={tag}
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
    for k, v in rep.items(): text = text.replace(k, v)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text.strip()

def create_pdf(text_content, recipe_title):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, clean_txt(recipe_title[:50]), ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", '', 11)
        
        is_step = False
        for line in text_content.split('\n'):
            l_clean = clean_txt(line)
            if not l_clean or '---' in l_clean: continue
            
            if 'zubereitung' in l_clean.lower():
                is_step = True
                pdf.ln(5); pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "ZUBEREITUNG:", ln=True); pdf.set_font("Arial", '', 11)
                continue

            if '|' in l_clean and not is_step:
                p = [i.strip() for i in l_clean.split('|') if i.strip()]
                if len(p) >= 2 and "zutat" not in p[1].lower():
                    pdf.cell(0, 7, f"- {p[0]} {p[1]}", ln=True)
            else:
                l_clean = l_clean.replace('**', '').replace('*', '')
                pdf.multi_cell(0, 7, l_clean)
        
        return pdf.output(dest='S').encode('latin-1')
    except:
        return None

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")

# Logo in Sidebar mit Design
st.markdown("<style>[data-testid='stSidebar'] img { background-color: white; padding: 10px; border-radius: 12px; margin-bottom: 20px; }</style>", unsafe_allow_html=True)

if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🍳 ChefList Pro")
    st.markdown(f'''<a href="{pay_link_90c}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold;">⚡ Unterstützen (0,90€)</button></a>''', unsafe_allow_html=True)
    st.divider()
    with st.expander("ℹ️ Rechtliches"):
        st.caption("Betreiber: Markus Simmel | Kontakt: legemasim@gmail.com")
        st.caption("Amazon-Partner: Ich verdiene an qualifizierten Verkäufen.")
        st.caption("Datenschutz: Keine Speicherung, verschlüsselte Verarbeitung.")

st.title("🍲 ChefList Pro")

video_url = st.text_input("YouTube Link:", placeholder="Link einfügen...")
c1, c2 = st.columns(2)
portions = c1.slider("Portionen:", 1, 10, 4)
unit_system = c2.radio("System:", ["Metrisch (g/ml)", "US-Einheiten (cups/oz)"], horizontal=True)

if st.button("Rezept erstellen ✨", use_container_width=True):
    if video_url:
        with st.spinner(f"Rechne Rezept auf {portions} Personen um..."):
            t, trans, d = get_full_video_data(video_url)
            st.session_state.recipe_title = t
            res = generate_smart_recipe(trans, d, amazon_tag, portions, unit_system)
            st.session_state.recipe_result = res

if st.session_state.recipe_result:
    st.divider()
    st.subheader(st.session_state.recipe_title)
    st.markdown(st.session_state.recipe_result)
    
    st.divider()
    pdf_data = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title)
    if pdf_data:
        st.download_button("📄 PDF herunterladen", pdf_data, file_name="Rezept.pdf", mime="application/pdf", use_container_width=True)
