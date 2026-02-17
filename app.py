import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. INTERNATIONALE KONFIGURATION (Alles basiert auf deinem Sidebar-Text) ---
LANG_CONFIG = {
    "English": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "en",
        "btn_pay": "⚡ Support ChefList Pro ($0.90)",
        "ui_header": "Convert YouTube recipes into printable PDFs",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Servings:", "ui_units": "Unit System:", "ui_create": "Create Recipe ✨",
        "ui_wait": "Calculating recipe for {0} servings...", "ui_ready": "Ready!",
        "ui_dl": "📄 Download PDF Recipe", "ui_buy": "Buy on Amazon*",
        "ui_counter_text": "Recipes created:",
        "ui_fb_header": "Help us improve! 🍲", "ui_fb_btn": "Send Feedback ✨",
        "ui_fb_placeholder": "What can we do better? (Errors, wishes, ideas)",
        "ui_fb_mail": "Your email (optional, if you want a reply)", "ui_fb_success": "Thank you! Your feedback has been saved. 🙌",
        "legal_title": "About & Legal", "legal_op": "**Operator:** Markus Simmel", 
        "legal_contact": "**Contact:** legemasim@gmail.com", "legal_total": "Total recipes generated:", 
        "legal_amz": "✨ As an Amazon Associate, I earn from qualifying purchases.",
        "legal_privacy_title": "🛡️ Data Protection", "legal_privacy_body": "We do not store personal data. Processing is encrypted.",
        "legal_note": "⚠️ **Note:** This app uses AI. AI can make mistakes – please verify cooking times and temperatures.",
        "admin_label": "🔑 Admin Access"
    },
    "Deutsch": {
        "tag": "cheflist21-21", "amz": "amazon.de", "curr": "EUR", "iso": "de",
        "btn_pay": "⚡ ChefList Pro unterstützen (0,90€)",
        "ui_header": "YouTube-Rezepte in druckbare PDFs verwandeln",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Portionen:", "ui_units": "Einheitensystem:", "ui_create": "Rezept erstellen ✨",
        "ui_wait": "Berechne Rezept für {0} Portionen...", "ui_ready": "Bereit!",
        "ui_dl": "📄 PDF Rezept herunterladen", "ui_buy": "Auf Amazon kaufen*",
        "ui_counter_text": "Erstellte Rezepte:",
        "ui_fb_header": "Hilf uns besser zu werden! 🍲", "ui_fb_btn": "Feedback senden ✨",
        "ui_fb_placeholder": "Was können wir besser machen? (Fehler, Wünsche, Ideen)",
        "ui_fb_mail": "Deine E-Mail (optional, für Rückfragen)", "ui_fb_success": "Danke! Dein Feedback wurde gespeichert. 🙌",
        "legal_title": "Über & Rechtliches", "legal_op": "**Betreiber:** Markus Simmel", 
        "legal_contact": "**Kontakt:** legemasim@gmail.com", "legal_total": "Bereits generierte Rezepte:", 
        "legal_amz": "✨ Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.",
        "legal_privacy_title": "🛡️ Datenschutz & Sicherheit", "legal_privacy_body": "Wir speichern keine persönlichen Daten. Die Verarbeitung erfolgt verschlüsselt.",
        "legal_note": "⚠️ **Hinweis:** Diese App nutzt eine KI. KI kann Fehler machen – bitte prüfe die Angaben.",
        "admin_label": "🔑 Admin Login"
    }
}
# (Weitere Sprachen folgen demselben Schema für die volle Vollständigkeit)

# --- 2. CONFIGURATION & API ---
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = None

paypal_email = "legemasim@gmail.com"

if not api_key:
    st.error("Please add your OpenAI API Key to Streamlit Secrets!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- GLOBAL COUNTER (Basierend auf deinem Code) ---
def update_global_counter():
    file_path = "total_recipes_global.txt"
    try:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f: f.write("0")
        with open(file_path, "r") as f: count = int(f.read())
        count += 1
        with open(file_path, "w") as f: f.write(str(count))
        return count
    except: return 0

def get_total_count():
    file_path = "total_recipes_global.txt"
    base_value = 17 
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f: return int(f.read()) + base_value
        except: return base_value
    return base_value

# --- 3. HELPER FUNCTIONS ---
def get_full_video_data(video_url):
    try:
        ydl_opts = {
            'quiet': True, 'skip_download': True, 'writesubtitles': True, 
            'writeautomaticsub': True, 'subtitleslangs': ['en', 'de', 'es', 'fr', 'it', 'pt']
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        video_title = info.get('title', 'Recipe')
        channel_name = info.get('uploader', 'Unknown Chef')
        description = info.get('description', '') 
        subs = info.get('subtitles') or info.get('automatic_captions')
        transcript = ""
        if subs:
            target_url = None
            for lang in ['en', 'de', 'es', 'fr', 'it', 'pt']:
                if lang in subs:
                    for f in subs[lang]:
                        if f.get('ext') == 'json3': target_url = f.get('url'); break
                    if target_url: break
            if target_url:
                res = requests.get(target_url)
                if res.status_code == 200:
                    data = res.json()
                    transcript = " ".join([seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])
        return video_title, transcript, description, channel_name
    except Exception as e:
        return "Recipe", None, None, "Unknown Chef"

def generate_smart_recipe(video_title, channel_name, transcript, description, config, portions, unit_system, lang_name):
    combined_input = f"ORIGINAL TITLE: {video_title}\nSOURCE CHANNEL: {channel_name}\n\nTRANSCRIPT:\n{transcript}\n\nDESCRIPTION:\n{description}"
    unit_instruction = "US UNITS (cups, oz, lbs, tsp, tbsp). If the source is metric, CONVERT to US units!" if unit_system == "US Units (cups/oz)" else "METRIC (g, ml, kg, l)."
    
    system_prompt = f"""
    You are a professional chef.
    1. Respond ENTIRELY in {lang_name}.
    2. Recalculate quantities for exactly {portions} person(s).
    3. Use {unit_instruction}
    4. Format Title: "[Recipe Name] by [Channel]"
    5. Table columns: Amount | Ingredient | Shop (Link: https://www.{config['amz']}/s?k=[INGREDIENT]&tag={config['tag']})
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input[:16000]}]
        )
        return response.choices[0].message.content
    except: return None

# --- 4. PDF GENERATOR ---
def clean_for_pdf(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'Euro'}
    for char, replacement in replacements.items(): text = text.replace(char, replacement)
    text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('–', '-')
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text

def create_pdf(text_content, recipe_title):
    try:
        pdf = FPDF()
        pdf.set_left_margin(10); pdf.set_right_margin(10); pdf.add_page()
        pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", style="B", size=14)
        display_title = clean_for_pdf(recipe_title[:40])
        pdf.cell(190, 15, txt=f"Recipe: {display_title}", ln=True, align='C', fill=True)
        pdf.ln(5); pdf.set_font("Arial", size=10)
        pdf.multi_cell(185, 7, txt=clean_for_pdf(text_content))
        return pdf.output()
    except: return None

# --- 5. INTERFACE & LOGIK ---
st.set_page_config(page_title="ChefList Pro Global", page_icon="🍲", layout="centered")

# CSS: Einzeiliger Button & Logo Styling
st.markdown("<style>.stButton>button { font-size: 12px !important; } [data-testid='stSidebar'] img { background-color: white; padding: 10px; border-radius: 12px; border: 2px solid #e0e0e0; margin-bottom: 20px; }</style>", unsafe_allow_html=True)

# Automatische Spracherkennung (Einmalig beim Start)
if "user_lang" not in st.session_state:
    try:
        # Browser-Header abfragen
        accept_lang = st.context.headers.get("Accept-Language", "en")
        detected = accept_lang.split(",")[0].split("-")[0].lower()
        st.session_state.user_lang = "Deutsch" if detected == "de" else "English"
    except:
        st.session_state.user_lang = "English"

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None

with st.sidebar:
    selected_language = st.selectbox("🌍 Language", list(LANG_CONFIG.keys()), index=list(LANG_CONFIG.keys()).index(st.session_state.user_lang))
    c = LANG_CONFIG[selected_language]
    
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🍳 ChefList Pro")
    
    st.info(f"{c['ui_counter_text']} {st.session_state.counter}")
    
    pay_link = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Support&amount=0.90&currency_code={c['curr']}"
    st.markdown(f'''<a href="{pay_link}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 8px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 11px; width: 100%;">{c['btn_pay']}</button></a>''', unsafe_allow_html=True)

    # Feedback Indicator
    new_fb = " 🔴" if os.path.exists("user_feedback.txt") and os.path.getsize("user_feedback.txt") > 0 else ""
    st.markdown("---")
    
    with st.expander(f"ℹ️ {c['legal_title']}{new_fb}"):
        st.caption(c["legal_op"])
        st.caption(c["legal_contact"])
        st.divider()
        st.write(f"📊 {c['legal_total']} **{get_total_count()}**")
        st.divider()
        st.caption(c["legal_amz"])
        st.divider()
        st.subheader(c["legal_privacy_title"])
        st.caption(c["legal_privacy_body"])
        st.divider()
        st.caption(c["legal_note"])
        st.divider()
        
        if st.checkbox(c["admin_label"]):
            admin_pw = st.text_input("Password", type="password", key="admin_pw_key")
            if admin_pw == "Gemini_Cheflist_pw":
                if os.path.exists("user_feedback.txt"):
                    with open("user_feedback.txt", "r") as f: st.text_area("Feedback Log:", value=f.read(), height=200)
                    if st.button("Clear Log"):
                        with open("user_feedback.txt", "w") as f: f.write(""); st.rerun()

# --- MAIN UI ---
st.title("🍲 ChefList Pro")
st.subheader(c['ui_header'])

v_url = st.text_input(c['ui_input_label'], placeholder="https://www.youtube.com/watch?v=...")
col1, col2 = st.columns(2)
ports = col1.slider(c['ui_servings'], 1, 10, 4)
units = col2.radio(c['ui_units'], ["Metric (g/ml)", "US Units (cups/oz)"], horizontal=True)

if st.button(c['ui_create'], use_container_width=True):
    if v_url:
        with st.status(c['ui_wait'].format(ports), expanded=True) as status:
            title_orig, transcript, description, channel = get_full_video_data(v_url)
            if transcript or description:
                res = generate_smart_recipe(title_orig, channel, transcript, description, c, ports, units, selected_language)
                if res:
                    st.session_state.recipe_result = res
                    st.session_state.recipe_title = title_orig
                    st.session_state.counter += 1
                    update_global_counter()
                    status.update(label=c['ui_ready'], state="complete", expanded=False)
                else: st.error("AI Error.")
            else: st.error("No data.")

if st.session_state.recipe_result:
    st.divider()
    # Titel aus dem Result extrahieren oder State nutzen
    st.subheader(f"📖 {st.session_state.get('recipe_title', 'Recipe')}")
    st.markdown(st.session_state.recipe_result.replace("Check on Amazon", c['ui_buy']))
    
    pdf_bytes = create_pdf(st.session_state.recipe_result, st.session_state.get("recipe_title", "Recipe"))
    if pdf_bytes:
        st.download_button(c['ui_dl'], pdf_bytes, file_name="Recipe.pdf", mime="application/pdf", use_container_width=True)

# --- FEEDBACK FORM ---
st.divider()
st.subheader(c['ui_fb_header'])
with st.form("fb_form"):
    fb_text = st.text_area(c['ui_fb_placeholder'])
    fb_mail = st.text_input(c['ui_fb_mail'])
    if st.form_submit_button(c['ui_fb_btn']):
        if fb_text:
            with open("user_feedback.txt", "a") as f:
                f.write(f"[{selected_language}] {fb_mail}: {fb_text}\n---\n")
            st.success(c['ui_fb_success'])
