import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. INTERNATIONALE KONFIGURATION ---
LANG_CONFIG = {
    "English": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD",
        "btn_pay": "⚡ Support ChefList Pro ($0.90)",
        "ui_servings": "Servings:", "ui_units": "Unit System:", "ui_create": "Create Recipe ✨",
        "ui_wait": "Calculating recipe...", "ui_ready": "Ready!",
        "ui_dl": "📄 Download PDF Recipe", "ui_buy": "Buy on Amazon*",
        "ui_counter_text": "Recipes created:", "iso": "en"
    },
    "Deutsch": {
        "tag": "cheflist21-21", "amz": "amazon.de", "curr": "EUR",
        "btn_pay": "⚡ ChefList Pro unterstützen (0,90€)",
        "ui_servings": "Portionen:", "ui_units": "Einheitensystem:", "ui_create": "Rezept jetzt erstellen ✨",
        "ui_wait": "Berechne Rezept...", "ui_ready": "Bereit!",
        "ui_dl": "📄 PDF Rezept herunterladen", "ui_buy": "Auf Amazon kaufen*",
        "ui_counter_text": "Erstellte Rezepte:", "iso": "de"
    },
    "Español": {"tag": "cheflist21-20", "amz": "amazon.es", "curr": "EUR", "btn_pay": "⚡ Apoyar ChefList Pro (0,90€)", "ui_servings": "Porciones:", "ui_units": "Unidades:", "ui_create": "Crear receta ✨", "ui_wait": "Calculando...", "ui_ready": "¡Listo!", "ui_dl": "📄 Descargar PDF", "ui_buy": "Comprar en Amazon*", "ui_counter_text": "Recetas:", "iso": "es"},
    "Français": {"tag": "cheflist21-20", "amz": "amazon.fr", "curr": "EUR", "btn_pay": "⚡ Soutenir ChefList Pro (0,90€)", "ui_servings": "Portions:", "ui_units": "Unités:", "ui_create": "Créer la recette ✨", "ui_wait": "Calcul...", "ui_ready": "Prêt !", "ui_dl": "📄 Télécharger le PDF", "ui_buy": "Acheter sur Amazon*", "ui_counter_text": "Recettes:", "iso": "fr"},
    "Italiano": {"tag": "cheflist21-20", "amz": "amazon.it", "curr": "EUR", "btn_pay": "⚡ Sostieni ChefList Pro (0,90€)", "ui_servings": "Porzioni:", "ui_units": "Unità:", "ui_create": "Crea ricetta ✨", "ui_wait": "Calcolo...", "ui_ready": "Pronto!", "ui_dl": "📄 Scarica PDF", "ui_buy": "Acquista su Amazon*", "ui_counter_text": "Ricette:", "iso": "it"},
    "Português": {"tag": "cheflist21-20", "amz": "amazon.com.br", "curr": "BRL", "btn_pay": "⚡ Apoiar ChefList Pro (R$4,50)", "ui_servings": "Porções:", "ui_units": "Unidades:", "ui_create": "Criar receita ✨", "ui_wait": "Calculando...", "ui_ready": "Pronto!", "ui_dl": "📄 Baixar PDF", "ui_buy": "Comprar na Amazon*", "ui_counter_text": "Recetas:", "iso": "pt"},
    "Nederlands": {"tag": "cheflist21-20", "amz": "amazon.nl", "curr": "EUR", "btn_pay": "⚡ Steun ChefList Pro (0,90€)", "ui_servings": "Porties:", "ui_units": "Eenheden:", "ui_create": "Recept maken ✨", "ui_wait": "Berekenen...", "ui_ready": "Klaar!", "ui_dl": "📄 PDF downloaden", "ui_buy": "Koop op Amazon*", "ui_counter_text": "Recepten:", "iso": "nl"},
    "Polski": {"tag": "cheflist21-20", "amz": "amazon.pl", "curr": "PLN", "btn_pay": "⚡ Wesprzyj ChefList Pro (4 PLN)", "ui_servings": "Porcje:", "ui_units": "Jednostki:", "ui_create": "Utwórz przepis ✨", "ui_wait": "Obliczanie...", "ui_ready": "Gotowe!", "ui_dl": "📄 Pobierz PDF", "ui_buy": "Kup na Amazon*", "ui_counter_text": "Przepisy:", "iso": "pl"},
    "Türkçe": {"tag": "cheflist21-20", "amz": "amazon.com.tr", "curr": "TRY", "btn_pay": "⚡ Destek ChefList Pro (30 TL)", "ui_servings": "Porsiyon:", "ui_units": "Birimler:", "ui_create": "Tarif oluştur ✨", "ui_wait": "Hesaplanıyor...", "ui_ready": "Hazır!", "ui_dl": "📄 PDF İndir", "ui_buy": "Amazon'dan satın al*", "ui_counter_text": "Tarifler:", "iso": "tr"},
    "日本語": {"tag": "cheflist21-20", "amz": "amazon.co.jp", "curr": "JPY", "btn_pay": "⚡ 支援 ChefList Pro (¥140)", "ui_servings": "人数:", "ui_units": "単位:", "ui_create": "レシピを作成 ✨", "ui_wait": "計算中...", "ui_ready": "完了！", "ui_dl": "📄 PDFをダウンロード", "ui_buy": "Amazonで購入*", "ui_counter_text": "レシピ数:", "iso": "ja"}
}

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

# --- GLOBAL COUNTER ---
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
            with open(file_path, "r") as f: 
                return int(f.read()) + base_value
        except: return base_value
    return base_value

# --- 3. HELPER FUNCTIONS ---
def get_full_video_data(video_url):
    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'writesubtitles': True, 'writeautomaticsub': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        video_title = info.get('title', 'Recipe')
        channel_name = info.get('uploader', 'Unknown Chef')
        description = info.get('description', '') 
        subs = info.get('subtitles') or info.get('automatic_captions')
        transcript = ""
        if subs:
            target_url = None
            for lang in ['en', 'de', 'es', 'fr', 'it', 'pt', 'ja', 'tr', 'pl', 'nl']:
                if lang in subs:
                    for f in subs[lang]:
                        if f.get('ext') == 'json3':
                            target_url = f.get('url'); break
                    if target_url: break
            if target_url:
                res = requests.get(target_url)
                if res.status_code == 200:
                    data = res.json()
                    transcript = " ".join([seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])
        return video_title, transcript, description, channel_name
    except:
        return "Recipe", None, None, "Unknown Chef"

def generate_smart_recipe(video_title, channel_name, transcript, description, config, portions, unit_system, lang_name):
    combined_input = f"ORIGINAL TITLE: {video_title}\nSOURCE CHANNEL: {channel_name}\n\nTRANSCRIPT:\n{transcript}\n\nDESCRIPTION:\n{description}"
    unit_instr = "US UNITS (cups, oz, lbs, tsp, tbsp)" if unit_system == "US Units (cups/oz)" else "METRIC (g, ml, kg, l)"
    
    system_prompt = f"""
    You are a professional chef. 
    TASK: Translate and convert the recipe for {portions} person(s).
    LANGUAGE: Respond ENTIRELY in {lang_name}.
    UNITS: {unit_instr}.
    STRUCTURE: 
    - TITLE: "[Recipe Name] by [Author/Channel]"
    - Key Data (Time, Difficulty, Servings: {portions})
    - Ingredients Table (Amount | Ingredient | Shop)
      -> Link: https://www.{config['amz']}/s?k=[INGREDIENTNAME]&tag={config['tag']}
    - Step-by-step Instructions.
    Start directly with the TITLE."""

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
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
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

# --- 5. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro Global", page_icon="🍲", layout="centered")

# CSS: Einzeiliger Spendenbutton & Logo Styling
st.markdown("<style>.stButton>button { font-size: 14px !important; } [data-testid='stSidebar'] img { background-color: white; padding: 10px; border-radius: 12px; border: 2px solid #e0e0e0; margin-bottom: 20px; }</style>", unsafe_allow_html=True)

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None

# --- AUTOMATISCHE SPRACHERKENNUNG BEIM ERSTEN START ---
if "detected_lang" not in st.session_state:
    try:
        # Wir fragen den Browser nach der bevorzugten Sprache (z.B. "de-DE,de;q=0.9")
        browser_lang = st.context.headers.get("Accept-Language", "en").split(",")[0].split("-")[0].lower()
        # Mapping auf unsere Liste
        detected = "English" # Default
        for name, cfg in LANG_CONFIG.items():
            if cfg["iso"] == browser_lang:
                detected = name
                break
        st.session_state.detected_lang = detected
    except:
        st.session_state.detected_lang = "English"

with st.sidebar:
    # Sprachauswahl (Vorbelegt mit erkannter Sprache)
    selected_language = st.selectbox("🌍 Language", list(LANG_CONFIG.keys()), index=list(LANG_CONFIG.keys()).index(st.session_state.detected_lang))
    c = LANG_CONFIG[selected_language]
    
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🍳 ChefList Pro")
    
    st.info(f"{c['ui_counter_text']} {st.session_state.counter}")
    
    pay_link = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Support&amount=0.90&currency_code={c['curr']}"
    st.markdown(f'''<a href="{pay_link}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 11px; width: 100%;">{c['btn_pay']}</button></a>''', unsafe_allow_html=True)

    # Feedback Indicator
    new_fb = " 🔴" if os.path.exists("user_feedback.txt") and os.path.getsize("user_feedback.txt") > 0 else ""
    st.markdown("---")
    
    with st.expander(f"ℹ️ About & Legal{new_fb}"):
        st.caption(f"**Operator:** Markus Simmel\n\n**Contact:** legemasim@gmail.com")
        st.divider()
        st.write(f"📊 Total recipes generated: **{get_total_count()}**")
        st.divider()
        st.caption("✨ As an Amazon Associate, I earn from qualifying purchases.")
        st.divider()
        st.subheader("🛡️ Data Protection")
        st.caption("We do not store personal data. Processing is encrypted.")
        st.divider()
        st.caption("⚠️ **Note:** AI can make mistakes – please verify results.")
        st.divider()
        
        if st.checkbox("🔑 Admin Access"):
            admin_pw = st.text_input("Password", type="password", key="admin_pw_global")
            if admin_pw == "Gemini_Cheflist_pw":
                if os.path.exists("user_feedback.txt"):
                    with open("user_feedback.txt", "r") as f: content = f.read()
                    st.text_area("Feedback Log:", value=content, height=200)
                    if st.button("Clear Log"):
                        with open("user_feedback.txt", "w") as f: f.write("")
                        st.rerun()

# --- MAIN UI ---
st.title("🍲 ChefList Pro")
st.subheader("Convert YouTube recipes into printable PDFs")

v_url = st.text_input("YouTube Video URL:", placeholder="https://...")
col1, col2 = st.columns(2)
ports = col1.slider(c['ui_servings'], 1, 10, 4)
units = col2.radio(c['ui_units'], ["Metric (g/ml)", "US Units (cups/oz)"], horizontal=True)

if st.button(c['ui_create'], use_container_width=True):
    if v_url:
        with st.status(c['ui_wait']) as status:
            t_orig, trans, desc, chef = get_full_video_data(v_url)
            if trans or desc:
                res = generate_smart_recipe(t_orig, chef, trans, desc, c, ports, units, selected_language)
                if res:
                    st.session_state.recipe_result = res
                    st.session_state.recipe_title = t_orig
                    st.session_state.counter += 1
                    update_global_counter()
                    status.update(label=c['ui_ready'], state="complete")

if st.session_state.get("recipe_result"):
    st.divider()
    st.markdown(st.session_state.recipe_result.replace("Check on Amazon", c['ui_buy']))
    pdf_bytes = create_pdf(st.session_state.recipe_result, st.session_state.get("recipe_title", "Recipe"))
    if pdf_bytes:
        st.download_button(c['ui_dl'], pdf_bytes, file_name="Recipe.pdf", mime="application/pdf", use_container_width=True)

st.divider()
st.subheader("Help us improve! 🍲")
with st.form("fb"):
    fb_text = st.text_area("Feedback:")
    fb_mail = st.text_input("Email (optional)")
    if st.form_submit_button("Send"):
        if fb_text:
            with open("user_feedback.txt", "a") as f: f.write(f"Lang: {selected_language} | {fb_mail}: {fb_text}\n---\n")
            st.success("Saved!")
