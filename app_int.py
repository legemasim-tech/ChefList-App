import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. INTERNATIONALE KONFIGURATION ---
# Hier definieren wir alle länderspezifischen Daten zentral
LANG_CONFIG = {
    "English": {
        "amz_host": "amazon.com", "tag": "cheflist21-20", "curr": "USD", "code": "en",
        "ui_title": "ChefList Pro", "ui_sub": "Convert YouTube recipes into printable PDFs",
        "ui_input": "YouTube Video URL:", "ui_btn": "Create Recipe ✨", "ui_portions": "Servings:",
        "ui_units": "Unit System:", "ui_dl": "📄 Download PDF Recipe", "ui_fb_header": "Help us improve! 🍲",
        "ui_fb_btn": "Send Feedback ✨", "ui_admin": "🔑 Admin Access", "ui_counter": "Recipes created:",
        "ui_ready": "Ready!", "ui_wait": "Calculating recipe...", "ui_buy": "Buy on Amazon"
    },
    "Deutsch": {
        "amz_host": "amazon.de", "tag": "cheflist21-21", "curr": "EUR", "code": "de",
        "ui_title": "ChefList Pro", "ui_sub": "Verwandle YouTube-Videos in druckbare PDFs",
        "ui_input": "YouTube Video URL:", "ui_btn": "Rezept jetzt erstellen ✨", "ui_portions": "Portionen:",
        "ui_units": "Einheitensystem:", "ui_dl": "📄 PDF Rezept herunterladen", "ui_fb_header": "Hilf uns besser zu werden! 🍲",
        "ui_fb_btn": "Feedback senden ✨", "ui_admin": "🔑 Admin Login", "ui_counter": "Deine Rezepte:",
        "ui_ready": "Bereit!", "ui_wait": "Berechne Rezept...", "ui_buy": "Auf Amazon kaufen"
    },
    "Español": {
        "amz_host": "amazon.es", "tag": "cheflist21-20", "curr": "EUR", "code": "es",
        "ui_title": "ChefList Pro", "ui_sub": "Convierte videos de YouTube en recetas PDF",
        "ui_input": "URL del video de YouTube:", "ui_btn": "Crear receta ahora ✨", "ui_portions": "Porciones:",
        "ui_units": "Sistema de unidades:", "ui_dl": "📄 Descargar receta en PDF", "ui_fb_header": "¡Ayúdanos a mejorar! 🍲",
        "ui_fb_btn": "Enviar comentarios ✨", "ui_admin": "🔑 Acceso Admin", "ui_counter": "Recetas creadas:",
        "ui_ready": "¡Listo!", "ui_wait": "Calculando receta...", "ui_buy": "Comprar en Amazon"
    },
    "Français": {
        "amz_host": "amazon.fr", "tag": "cheflist21-20", "curr": "EUR", "code": "fr",
        "ui_title": "ChefList Pro", "ui_sub": "Transformez vos vidéos YouTube en PDF",
        "ui_input": "URL de la vidéo YouTube :", "ui_btn": "Créer la recette ✨", "ui_portions": "Portions :",
        "ui_units": "Système d'unités :", "ui_dl": "📄 Télécharger la recette PDF", "ui_fb_header": "Aidez-nous à nous améliorer ! 🍲",
        "ui_fb_btn": "Envoyer ✨", "ui_admin": "🔑 Accès Admin", "ui_counter": "Recettes créées :",
        "ui_ready": "Prêt !", "ui_wait": "Calcul de la recette...", "ui_buy": "Acheter sur Amazon"
    },
    "Italiano": {
        "amz_host": "amazon.it", "tag": "cheflist21-20", "curr": "EUR", "code": "it",
        "ui_title": "ChefList Pro", "ui_sub": "Trasforma i video di YouTube in PDF stampabili",
        "ui_input": "URL del video YouTube:", "ui_btn": "Crea ricetta ora ✨", "ui_portions": "Porzioni:",
        "ui_units": "Sistema di unità:", "ui_dl": "📄 Scarica la ricetta in PDF", "ui_fb_header": "Aiutaci a migliorare! 🍲",
        "ui_fb_btn": "Invia feedback ✨", "ui_admin": "🔑 Accesso Admin", "ui_counter": "Ricette create:",
        "ui_ready": "Pronto!", "ui_wait": "Calcolo della ricetta...", "ui_buy": "Acquista su Amazon"
    },
    "Português": {
        "amz_host": "amazon.com.br", "tag": "cheflist21-20", "curr": "BRL", "code": "pt",
        "ui_title": "ChefList Pro", "ui_sub": "Transforme vídeos do YouTube em PDFs",
        "ui_input": "URL do vídeo do YouTube:", "ui_btn": "Criar receita agora ✨", "ui_portions": "Porções:",
        "ui_units": "Sistema de unidades:", "ui_dl": "📄 Baixar receita em PDF", "ui_fb_header": "Ajude-nos a melhorar! 🍲",
        "ui_fb_btn": "Enviar feedback ✨", "ui_admin": "🔑 Acesso Admin", "ui_counter": "Receitas criadas:",
        "ui_ready": "Pronto!", "ui_wait": "Calculando receita...", "ui_buy": "Comprar na Amazon"
    },
    "Nederlands": {
        "amz_host": "amazon.nl", "tag": "cheflist21-20", "curr": "EUR", "code": "nl",
        "ui_title": "ChefList Pro", "ui_sub": "Zet YouTube-video's om in PDF-recepten",
        "ui_input": "YouTube-video-URL:", "ui_btn": "Recept maken ✨", "ui_portions": "Porties:",
        "ui_units": "Eenheden:", "ui_dl": "📄 PDF downloaden", "ui_fb_header": "Help ons verbeteren! 🍲",
        "ui_fb_btn": "Verstuur ✨", "ui_admin": "🔑 Admin toegang", "ui_counter": "Recepten gemaakt:",
        "ui_ready": "Klaar!", "ui_wait": "Berekenen...", "ui_buy": "Koop op Amazon"
    },
    "Türkçe": {
        "amz_host": "amazon.com.tr", "tag": "cheflist21-20", "curr": "TRY", "code": "tr",
        "ui_title": "ChefList Pro", "ui_sub": "YouTube videolarını PDF tariflerine dönüştürün",
        "ui_input": "YouTube Video URL'si:", "ui_btn": "Tarifi oluştur ✨", "ui_portions": "Porsiyon:",
        "ui_units": "Birim Sistemi:", "ui_dl": "📄 PDF Tarifini İndir", "ui_fb_header": "Gelişmemize yardımcı olun! 🍲",
        "ui_fb_btn": "Geri bildirim gönder ✨", "ui_admin": "🔑 Admin Girişi", "ui_counter": "Oluşturulan tarifler:",
        "ui_ready": "Hazır!", "ui_wait": "Tarif hesaplanıyor...", "ui_buy": "Amazon'dan satın al"
    },
    "日本語": {
        "amz_host": "amazon.co.jp", "tag": "cheflist21-20", "curr": "JPY", "code": "ja",
        "ui_title": "ChefList Pro", "ui_sub": "YouTube動画を印刷可能なPDFに変換",
        "ui_input": "YouTube動画のURL:", "ui_btn": "レシピを作成 ✨", "ui_portions": "人数:",
        "ui_units": "単位系:", "ui_dl": "📄 PDFレシピをダウンロード", "ui_fb_header": "改善にご協力ください！ 🍲",
        "ui_fb_btn": "フィードバックを送信 ✨", "ui_admin": "🔑 管理者アクセス", "ui_counter": "作成済みレシピ数:",
        "ui_ready": "完了！", "ui_wait": "レシピを計算中...", "ui_buy": "Amazonで購入"
    },
    "Polski": {
        "amz_host": "amazon.pl", "tag": "cheflist21-20", "curr": "PLN", "code": "pl",
        "ui_title": "ChefList Pro", "ui_sub": "Zmień filmy z YouTube w przepisy PDF",
        "ui_input": "URL filmu z YouTube:", "ui_btn": "Utwórz przepis ✨", "ui_portions": "Porcje:",
        "ui_units": "System jednostek:", "ui_dl": "📄 Pobierz przepis PDF", "ui_fb_header": "Pomóż nam się doskonalić! 🍲",
        "ui_fb_btn": "Wyślij ✨", "ui_admin": "🔑 Panel Admina", "ui_counter": "Utworzone przepisy:",
        "ui_ready": "Gotowe!", "ui_wait": "Obliczanie przepisu...", "ui_buy": "Kup na Amazon"
    }
}

# --- 2. CONFIGURATION & API ---
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = None

if not api_key:
    st.error("Missing OpenAI API Key in Streamlit Secrets!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- GLOBALER ZÄHLER ---
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
        ydl_opts = {
            'quiet': True, 'skip_download': True, 'writesubtitles': True, 
            'writeautomaticsub': True, 'subtitleslangs': ['en', 'de', 'es', 'fr', 'it', 'pt', 'ja', 'tr', 'pl', 'nl']
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        video_title = info.get('title', 'Recipe')
        description = info.get('description', '') 
        subs = info.get('subtitles') or info.get('automatic_captions')
        transcript = ""
        if subs:
            target_url = None
            # Suche nach passenden Untertiteln
            for lang_code in ['de', 'en', 'es', 'fr', 'it', 'pt', 'ja', 'tr', 'pl', 'nl']:
                if lang_code in subs:
                    for f in subs[lang_code]:
                        if f.get('ext') == 'json3':
                            target_url = f.get('url'); break
                    if target_url: break
            if target_url:
                res = requests.get(target_url)
                if res.status_code == 200:
                    data = res.json()
                    transcript = " ".join([seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])
        return video_title, transcript, description
    except:
        return "Recipe", None, None

def generate_smart_recipe(transcript, description, lang_name, portions, unit_system, config):
    combined_input = f"TRANSCRIPT:\n{transcript}\n\nDESCRIPTION:\n{description}"
    unit_instruction = "Metric (g/ml)" if unit_system in ["Metrisch (g/ml)", "Metric (g/ml)"] else "US-Units (cups/oz)"
    
    system_prompt = f"""
    You are a professional chef.
    TASK: Translate and convert the recipe from the video for {portions} person(s).
    LANGUAGE: Respond ENTIRELY in {lang_name}.
    UNITS: Use {unit_instruction}.
    AMAZON: Use https://www.{config['amz_host']}/s?k=[INGREDIENT]&tag={config['tag']} for the shop links.
    STRUCTURE: Title, Key Data, Ingredients Table (Amount | Ingredient | Shop), Instructions.
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
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    text = re.sub(r'[^\x00-\x7F]+', '', text) # Entfernt Unicode für Standard-PDF
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text

def create_pdf(text_content, recipe_title):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(190, 15, txt=clean_for_pdf(recipe_title[:40]), ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 7, txt=clean_for_pdf(text_content))
        return bytes(pdf.output())
    except: return None

# --- 5. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro Global", page_icon="🍲", layout="centered")

# --- SPRACHAUSWAHL ---
with st.sidebar:
    st.title("🌍 Global Settings")
    selected_language = st.selectbox("Choose Language:", list(LANG_CONFIG.keys()))
    c = LANG_CONFIG[selected_language] # c = Aktuelle Konfiguration
    
    st.divider()
    st.info(f"{c['ui_counter']} {st.session_state.get('counter', 0)}")
    
    # Dynamischer Bezahllink
    paypal_url = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=legemasim@gmail.com&item_name=ChefList_Pro&amount=0.90&currency_code={c['curr']}"
    st.markdown(f'''<a href="{paypal_url}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; width: 100%;">{c['ui_btn']} Support (0.90 {c['curr']})</button></a>''', unsafe_allow_html=True)

    # Feedback Indicator
    new_fb = " 🔴" if os.path.exists("user_feedback.txt") and os.path.getsize("user_feedback.txt") > 0 else ""
    st.markdown("---")
    with st.expander(f"ℹ️ Legal & Admin{new_fb}"):
        st.write(f"📊 Total Global: {get_total_count()}")
        if st.checkbox(c['ui_admin']):
            admin_pw = st.text_input("Password", type="password")
            if admin_pw == "Gemini_Cheflist_pw" and os.path.exists("user_feedback.txt"):
                with open("user_feedback.txt", "r") as f: st.text_area("Feedback Log:", f.read(), height=200)

# --- HAUPTBEREICH ---
st.title(f"🍲 {c['ui_title']}")
st.subheader(c['ui_sub'])

if "res" not in st.session_state: st.session_state.res = None
if "title" not in st.session_state: st.session_state.title = ""

v_url = st.text_input(c['ui_input'], placeholder="https://www.youtube.com/...")
col1, col2 = st.columns(2)
ports = col1.slider(c['ui_portions'], 1, 10, 4)
units = col2.radio(c['ui_units'], [c['ui_units'].split(':')[0], "US-Units"] if selected_language == "Deutsch" else ["Metric", "US-Units"], horizontal=True)

if st.button(c['ui_btn'], use_container_width=True):
    if v_url:
        with st.status(c['ui_wait']) as status:
            title, trans, desc = get_full_video_data(v_url)
            if trans or desc:
                res = generate_smart_recipe(trans, desc, selected_language, ports, units, c)
                st.session_state.res = res
                st.session_state.title = title
                st.session_state.counter = st.session_state.get('counter', 0) + 1
                update_global_counter()
                status.update(label=c['ui_ready'], state="complete")

if st.session_state.res:
    st.divider()
    st.subheader(f"📖 {st.session_state.title}")
    st.markdown(st.session_state.res.replace("Check on Amazon", c['ui_buy']))
    
    pdf_data = create_pdf(st.session_state.res, st.session_state.title)
    if pdf_data:
        st.download_button(c['ui_dl'], pdf_data, file_name="Recipe.pdf", mime="application/pdf", use_container_width=True)

# --- FEEDBACK ---
st.divider()
st.subheader(c['ui_fb_header'])
with st.form("fb_form"):
    fb_text = st.text_area("...")
    fb_mail = st.text_input("Email (optional)")
    if st.form_submit_button(c['ui_fb_btn']):
        if fb_text:
            with open("user_feedback.txt", "a") as f: f.write(f"Lang: {selected_language} | Mail: {fb_mail}\n{fb_text}\n---\n")
            st.success("Thank you! / Danke!")
