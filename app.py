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

# --- GLOBALER ZÄHLER ---
def update_global_counter():
    file_path = "total_recipes.txt"
    try:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f: f.write("0")
        with open(file_path, "r") as f: count = int(f.read())
        count += 1
        with open(file_path, "w") as f: f.write(str(count))
        return count
    except: return 0

def get_total_count():
    file_path = "total_recipes.txt"
    base_value = 17 
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f: 
                return int(f.read()) + base_value
        except: return base_value
    return base_value

# --- 2. HILFSFUNKTIONEN ---
def get_full_video_data(video_url):
    try:
        ydl_opts = {
            'quiet': True, 
            'skip_download': True, 
            'writesubtitles': True, 
            'writeautomaticsub': True, 
            'subtitleslangs': ['de', 'en', 'es', 'fr'] 
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        
        video_title = info.get('title', 'Rezept')
        description = info.get('description', '') 
        subs = info.get('subtitles') or info.get('automatic_captions')
        transcript = ""
        
        if subs:
            target_url = None
            for lang in ['de', 'en', 'es', 'fr']:
                if lang in subs:
                    for f in subs[lang]:
                        if f.get('ext') == 'json3':
                            target_url = f.get('url')
                            break
                    if target_url: break
            
            if target_url:
                res = requests.get(target_url)
                if res.status_code == 200:
                    data = res.json()
                    transcript = " ".join([
                        seg.get('utf8', '').strip() 
                        for event in data.get('events', []) 
                        if 'segs' in event 
                        for seg in event['segs'] 
                        if seg.get('utf8', '')
                    ])
        
        return video_title, transcript, description
    except:
        return "Rezept", None, None

def generate_smart_recipe(transcript, description, tag, portions, unit_system):
    combined_input = f"VIDEO DATEN:\n{transcript}\n\nBESCHREIBUNG:\n{description}"
    unit_instruction = "METRISCH (g/ml)" if unit_system == "Metrisch (g/ml)" else "US-Einheiten (cups/oz)"
    
    system_prompt = f"""
    Du bist ein Profi-Koch. Erstelle ein Rezept für {portions} Personen.
    NUTZE EINHEITEN: {unit_instruction}.
    STRUKTUR:
    1. Eckdaten (Dauer, Schwierigkeit)
    2. Tabelle: Menge | Zutat | Kaufen
       -> Link: https://www.amazon.de/s?k=[ZUTAT]&tag={tag}
    3. Schritt-für-Schritt Zubereitung.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input[:16000]}]
        )
        return response.choices[0].message.content
    except: return None

# --- 3. PDF GENERATOR (STABLE VERSION) ---
def clean_for_pdf(text):
    if not text: return ""
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'Euro', '–': '-', '—': '-'}
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    # Entfernt alle Symbole/Emojis/Nicht-ASCII Zeichen für FPDF Kompatibilität
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text

def create_pdf(text_content, recipe_title):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", style="B", size=16)
        
        # Header
        title = clean_for_pdf(recipe_title[:50])
        pdf.cell(0, 10, txt=f"Rezept: {title}", ln=True, align='C')
        pdf.ln(10)
        
        # Content
        pdf.set_font("Arial", size=11)
        clean_text = clean_for_pdf(text_content)
        pdf.multi_cell(0, 7, txt=clean_text)
        
        # Output als Bytes (Wichtig für Streamlit Cloud!)
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    except Exception as e:
        st.error(f"PDF Fehler: {e}")
        return None

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲", layout="centered")

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

with st.sidebar:
    st.title("🍳 ChefList Pro")
    st.info(f"Erstellte Rezepte: {st.session_state.counter}")
    st.markdown(f'''<a href="{pay_link_90c}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold;">⚡ ChefList Pro unterstützen (0,90€)</button></a>''', unsafe_allow_html=True)
    
    with st.expander("ℹ️ Über & Rechtliches"):
        st.write(f"📊 Gesamt Rezepte: {get_total_count()}")
        st.caption("Betreiber: Markus Simmel")

st.title("🍲 ChefList Pro")
video_url = st.text_input("YouTube Video URL:", placeholder="https://...")
col1, col2 = st.columns(2)
portions = col1.slider("Portionen:", 1, 10, 4)
unit_system = col2.radio("Einheiten:", ["Metrisch (g/ml)", "US-Einheiten (cups/oz)"], horizontal=True)

if st.button("Rezept jetzt erstellen ✨", use_container_width=True):
    if video_url:
        with st.status("Berechne Rezept...", expanded=True) as status:
            title, transcript, description = get_full_video_data(video_url)
            if transcript or description:
                result = generate_smart_recipe(transcript, description, amazon_tag, portions, unit_system)
                if result:
                    st.session_state.recipe_result = result
                    st.session_state.recipe_title = title
                    st.session_state.counter += 1
                    update_global_counter()
                    status.update(label="Fertig!", state="complete")
            else:
                st.error("Konnte keine Untertitel extrahieren.")

if st.session_state.recipe_result:
    st.divider()
    st.subheader(f"📖 {st.session_state.recipe_title}")
    st.markdown(st.session_state.recipe_result)
    
    # PDF Button
    pdf_bytes = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title)
    if pdf_bytes:
        st.download_button(
            label="📄 PDF Rezept herunterladen",
            data=pdf_bytes,
            file_name="ChefList_Rezept.pdf",
            mime="application/pdf",
            use_container_width=True
        )
