import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. INTERNATIONALE KONFIGURATION (VOLLSTÄNDIG) ---
# Jede Sprache hat exakt die gleichen Keys, damit keine KeyErrors entstehen.
LANG_CONFIG = {
    "English": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "en",
        "ui_header": "Convert YouTube recipes into printable PDFs",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Servings:", "ui_units": "Units:", 
        "ui_unit_opts": ["US Units (cups/oz)", "Metric (g/ml)"], # WICHTIG FÜR DEN FIX
        "ui_create": "Create Recipe ✨", "ui_wait": "Calculating for {0} servings...", "ui_ready": "Ready!",
        "ui_dl": "📄 Download PDF Recipe", "ui_buy": "Buy on Amazon*", "ui_counter": "Recipes created:",
        "legal_title": "About & Legal", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_amz": "✨ As an Amazon Associate, I earn from qualifying purchases.", "legal_note": "⚠️ AI can make mistakes.",
        "ai_lang": "ENGLISH", "fb_header": "Help us improve! 🍲", "fb_btn": "Send ✨", 
        "fb_place": "What can we do better?", "fb_mail": "Email (optional)", "fb_thx": "Saved! 🙌"
    },
    "Deutsch": {
        "tag": "cheflist21-21", "amz": "amazon.de", "curr": "EUR", "iso": "de",
        "ui_header": "YouTube-Rezepte in druckbare PDFs verwandeln",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Portionen:", "ui_units": "Einheiten:", 
        "ui_unit_opts": ["Metrisch (g/ml)", "US-Einheiten (cups/oz)"],
        "ui_create": "Rezept erstellen ✨", "ui_wait": "Berechne für {0} Portionen...", "ui_ready": "Bereit!",
        "ui_dl": "📄 PDF herunterladen", "ui_buy": "Auf Amazon kaufen*", "ui_counter": "Erstellte Rezepte:",
        "legal_title": "Über & Rechtliches", "legal_op": "**Betreiber:** Markus Simmel", "legal_contact": "**Kontakt:** legemasim@gmail.com",
        "legal_amz": "✨ Als Amazon-Partner verdiene ich an Käufen.", "legal_note": "⚠️ KI kann Fehler machen.",
        "ai_lang": "GERMAN", "fb_header": "Hilf uns besser zu werden! 🍲", "fb_btn": "Senden ✨",
        "fb_place": "Was können wir besser machen?", "fb_mail": "E-Mail (optional)", "fb_thx": "Gespeichert! 🙌"
    },
    "Español": {
        "tag": "cheflist21-20", "amz": "amazon.es", "curr": "EUR", "iso": "es", 
        "ui_header": "YouTube a PDF", "ui_input_label": "URL del video:", 
        "ui_servings": "Porciones:", "ui_units": "Unidades:", "ui_unit_opts": ["Métrico (g/ml)", "EE.UU. (cups/oz)"],
        "ui_create": "Crear ✨", "ui_wait": "Calculando...", "ui_ready": "¡Listo!", 
        "ui_dl": "📄 Descargar PDF", "ui_buy": "Comprar en Amazon*", "ui_counter": "Recetas:", 
        "legal_title": "Legal", "legal_op": "Markus Simmel", "legal_contact": "legemasim@gmail.com", 
        "legal_amz": "Socio Amazon.", "legal_note": "IA puede fallar.", "ai_lang": "SPANISH", 
        "fb_header": "¡Ayúdanos! 🍲", "fb_btn": "Enviar ✨", "fb_place": "¿Ideas?", "fb_mail": "Email", "fb_thx": "¡Gracias! 🙌"
    },
    "Français": {
        "tag": "cheflist21-20", "amz": "amazon.fr", "curr": "EUR", "iso": "fr", 
        "ui_header": "YouTube en PDF", "ui_input_label": "URL vidéo:", 
        "ui_servings": "Portions:", "ui_units": "Unités:", "ui_unit_opts": ["Métrique (g/ml)", "US (cups/oz)"],
        "ui_create": "Créer ✨", "ui_wait": "Calcul...", "ui_ready": "Prêt!", 
        "ui_dl": "📄 Télécharger PDF", "ui_buy": "Amazon*", "ui_counter": "Recettes:", 
        "legal_title": "Légal", "legal_op": "Simmel", "legal_contact": "legemasim@gmail.com", 
        "legal_amz": "Amazon.", "legal_note": "L'IA peut errer.", "ai_lang": "FRENCH", 
        "fb_header": "Aidez-nous! 🍲", "fb_btn": "Envoyer ✨", "fb_place": "Idées?", "fb_mail": "Email", "fb_thx": "Merci! 🙌"
    },
    "Italiano": {
        "tag": "cheflist21-20", "amz": "amazon.it", "curr": "EUR", "iso": "it", 
        "ui_header": "YouTube in PDF", "ui_input_label": "URL video:", 
        "ui_servings": "Porzioni:", "ui_units": "Unità:", "ui_unit_opts": ["Metrico (g/ml)", "US (cups/oz)"],
        "ui_create": "Crea ✨", "ui_wait": "Calcolo...", "ui_ready": "Pronto!", 
        "ui_dl": "📄 Scarica PDF", "ui_buy": "Amazon*", "ui_counter": "Ricette:", 
        "legal_title": "Legale", "legal_op": "Simmel", "legal_contact": "legemasim@gmail.com", 
        "legal_amz": "Amazon.", "legal_note": "IA può sbagliare.", "ai_lang": "ITALIAN", 
        "fb_header": "Aiutaci! 🍲", "fb_btn": "Invia ✨", "fb_place": "Idee?", "fb_mail": "Email", "fb_thx": "Grazie! 🙌"
    },
    "Português": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "pt", 
        "ui_header": "YouTube para PDF", "ui_input_label": "URL:", 
        "ui_servings": "Porções:", "ui_units": "Unidades:", "ui_unit_opts": ["Métrico (g/ml)", "US (cups/oz)"],
        "ui_create": "Criar ✨", "ui_wait": "Calculando...", "ui_ready": "Pronto!", 
        "ui_dl": "📄 Baixar PDF", "ui_buy": "Amazon*", "ui_counter": "Receitas:", 
        "legal_title": "Legal", "legal_op": "Simmel", "legal_contact": "legemasim@gmail.com", 
        "legal_amz": "Amazon.", "legal_note": "IA pode errar.", "ai_lang": "PORTUGUESE", 
        "fb_header": "Ajuda! 🍲", "fb_btn": "Enviar ✨", "fb_place": "Ideias?", "fb_mail": "Email", "fb_thx": "Obrigado! 🙌"
    },
    "Nederlands": {
        "tag": "cheflist21-20", "amz": "amazon.nl", "curr": "EUR", "iso": "nl", 
        "ui_header": "YouTube naar PDF", "ui_input_label": "URL:", 
        "ui_servings": "Porties:", "ui_units": "Eenheden:", "ui_unit_opts": ["Metrisch (g/ml)", "US (cups/oz)"],
        "ui_create": "Maken ✨", "ui_wait": "Wacht...", "ui_ready": "Klaar!", 
        "ui_dl": "📄 PDF download", "ui_buy": "Amazon*", "ui_counter": "Recepten:", 
        "legal_title": "Juridisch", "legal_op": "Simmel", "legal_contact": "legemasim@gmail.com", 
        "legal_amz": "Amazon.", "legal_note": "AI fout.", "ai_lang": "DUTCH", 
        "fb_header": "Help! 🍲", "fb_btn": "Verzend ✨", "fb_place": "Ideeën?", "fb_mail": "Email", "fb_thx": "Bedankt! 🙌"
    },
    "Polski": {
        "tag": "cheflist21-20", "amz": "amazon.pl", "curr": "PLN", "iso": "pl", 
        "ui_header": "YouTube na PDF", "ui_input_label": "URL:", 
        "ui_servings": "Porcje:", "ui_units": "Jednostki:", "ui_unit_opts": ["Metryczne (g/ml)", "US (cups/oz)"],
        "ui_create": "Utwórz ✨", "ui_wait": "Czekaj...", "ui_ready": "Gotowe!", 
        "ui_dl": "📄 Pobierz PDF", "ui_buy": "Amazon*", "ui_counter": "Przepisy:", 
        "legal_title": "Prawne", "legal_op": "Simmel", "legal_contact": "legemasim@gmail.com", 
        "legal_amz": "Amazon.", "legal_note": "Błąd AI.", "ai_lang": "POLISH", 
        "fb_header": "Pomoc! 🍲", "fb_btn": "Wyślij ✨", "fb_place": "Pomysły?", "fb_mail": "Email", "fb_thx": "Dzięki! 🙌"
    },
    "Türkçe": {
        "tag": "cheflist21-20", "amz": "amazon.com.tr", "curr": "TRY", "iso": "tr", 
        "ui_header": "YouTube'dan PDF'e", "ui_input_label": "URL:", 
        "ui_servings": "Porsiyon:", "ui_units": "Birimler:", "ui_unit_opts": ["Metrik (g/ml)", "ABD (cups/oz)"],
        "ui_create": "Oluştur ✨", "ui_wait": "Bekleyin...", "ui_ready": "Hazır!", 
        "ui_dl": "📄 PDF İndir", "ui_buy": "Amazon*", "ui_counter": "Tarifler:", 
        "legal_title": "Yasal", "legal_op": "Simmel", "legal_contact": "legemasim@gmail.com", 
        "legal_amz": "Amazon.", "legal_note": "AI hata.", "ai_lang": "TURKISH", 
        "fb_header": "Yardım! 🍲", "fb_btn": "Gönder ✨", "fb_place": "Fikirler?", "fb_mail": "E-posta", "fb_thx": "Teşekkürler! 🙌"
    },
    "日本語": {
        "tag": "cheflist21-20", "amz": "amazon.co.jp", "curr": "JPY", "iso": "ja", 
        "ui_header": "YouTubeをPDFに", "ui_input_label": "URL:", 
        "ui_servings": "人数:", "ui_units": "単位:", "ui_unit_opts": ["メートル法 (g/ml)", "US単位 (cups/oz)"],
        "ui_create": "作成 ✨", "ui_wait": "計算中...", "ui_ready": "完了！", 
        "ui_dl": "📄 PDF保存", "ui_buy": "Amazon*", "ui_counter": "レシピ数:", 
        "legal_title": "法的情報", "legal_op": "Simmel", "legal_contact": "legemasim@gmail.com", 
        "legal_amz": "Amazon.", "legal_note": "AIミス.", "ai_lang": "JAPANESE", 
        "fb_header": "改善にご協力ください 🍲", "fb_btn": "送信 ✨", "fb_place": "ご意見", "fb_mail": "メール", "fb_thx": "感謝! 🙌"
    }
}

# --- 2. KONFIGURATION & API ---
try: api_key = st.secrets["OPENAI_API_KEY"]
except: api_key = None
paypal_email = "legemasim@gmail.com"
if not api_key: st.error("Please add OpenAI API Key!"); st.stop()
client = openai.OpenAI(api_key=api_key)

# --- 3. HELPER FUNCTIONS ---
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

def get_full_video_data(video_url):
    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'writesubtitles': True, 'writeautomaticsub': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        video_title = info.get('title', 'Recipe')
        channel_name = info.get('uploader', 'Chef')
        description = info.get('description', '') 
        subs = info.get('subtitles') or info.get('automatic_captions')
        transcript = ""
        if subs:
            for lang in ['en', 'de', 'es', 'fr', 'it', 'pt', 'ja', 'tr', 'pl', 'nl']:
                if lang in subs:
                    for f in subs[lang]:
                        if f.get('ext') == 'json3':
                            res = requests.get(f.get('url'))
                            if res.status_code == 200:
                                transcript = " ".join([seg.get('utf8', '').strip() for event in res.json().get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])
                                break
                    if transcript: break
        return video_title, transcript, description, channel_name
    except: return "Recipe", None, None, "Chef"

def generate_smart_recipe(video_title, channel_name, transcript, description, config, portions, unit_system):
    # Einfache Logik für Einheiten
    u_inst = "US UNITS (cups, oz)" if "US" in unit_system or "EE.UU." in unit_system or "US" in str(unit_system) else "METRIC (g, ml)"
    
    system_prompt = f"""
    You are a professional chef. Respond in {config['ai_lang']}.
    Servings: {portions}. Units: {u_inst}.
    Format: "TITLE: [Recipe Name] by [Author]"
    Table: Amount | Ingredient | Shop (Link: https://www.{config['amz']}/s?k=[ITEM]&tag={config['tag']})
    """
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"TITLE: {video_title}\nTRANSCRIPT: {transcript[:12000]}"}])
        return response.choices[0].message.content
    except: return None

# --- PDF GENERATOR (ROBUST) ---
def clean_for_pdf(text):
    if not text: return ""
    # Standard Ersetzungen
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'Euro', '–': '-'}
    for char, rep in replacements.items(): text = text.replace(char, rep)
    # Entfernt ALLES was nicht ASCII ist (Emoji, Japanisch etc.), damit PDF nicht abstürzt
    return re.sub(r'[^\x00-\x7F]+', '', text)

def create_pdf(text_content, recipe_title):
    try:
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 10, txt=clean_for_pdf(recipe_title[:40]), ln=True, align='C')
        pdf.ln(5); pdf.set_font("Arial", size=10)
        
        for line in text_content.split('\n'):
            clean_line = clean_for_pdf(line.strip())
            if clean_line: pdf.multi_cell(0, 7, txt=clean_line)
            
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    except: return None

# --- 4. INTERFACE ---
st.set_page_config(page_title="ChefList Pro Global", page_icon="🍲")

# Automatik Logik (Session State init)
if "user_lang_selection" not in st.session_state:
    try:
        lang_header = st.context.headers.get("Accept-Language", "en")
        primary_code = lang_header.split(",")[0].split("-")[0].lower()
        mapping = {"de": "Deutsch", "en": "English", "es": "Español", "fr": "Français", "it": "Italiano", "pt": "Português", "nl": "Nederlands", "pl": "Polski", "tr": "Türkçe", "ja": "日本語"}
        st.session_state.user_lang_selection = mapping.get(primary_code, "English")
    except: st.session_state.user_lang_selection = "English"

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

with st.sidebar:
    # Sicherstellen, dass die Sprache in der Liste existiert
    try:
        idx = list(LANG_CONFIG.keys()).index(st.session_state.user_lang_selection)
    except: idx = 0
        
    selected_lang = st.selectbox("🌍 Language", list(LANG_CONFIG.keys()), index=idx)
    c = LANG_CONFIG[selected_lang]
    
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🍳 ChefList Pro")
    
    st.info(f"{c['ui_counter']} {st.session_state.counter}")
    pay_url = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&amount=0.90&currency_code={c['curr']}"
    st.markdown(f'''<a href="{pay_url}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 8px; border-radius: 5px; font-weight: bold; cursor: pointer;">⚡ Support (0.90 {c['curr']})</button></a>''', unsafe_allow_html=True)
    
    st.markdown("---")
    with st.expander(c["legal_title"]):
        st.caption(f"{c['legal_op']}\n\n{c['legal_contact']}\n\n📊 Total: {get_total_count()}\n\n{c['legal_amz']}\n\n{c['legal_note']}")
    
    if st.checkbox("Admin"):
        pw = st.text_input("PW", type="password")
        if pw == "Gemini_Cheflist_pw" and os.path.exists("user_feedback.txt"):
            with open("user_feedback.txt") as f: st.text_area("Log", f.read())

st.title("🍲 ChefList Pro")
st.subheader(c['ui_header'])

v_url = st.text_input(c['ui_input_label'], placeholder="https://...")
col1, col2 = st.columns(2)
ports = col1.slider(c['ui_servings'], 1, 10, 4)

# FIX: Hier greifen wir jetzt sicher auf die Liste zu
units = col2.radio(c['ui_units'], c['ui_unit_opts'], horizontal=True)

if st.button(c['ui_create'], use_container_width=True):
    if v_url:
        with st.status(c['ui_wait'].format(ports)) as status:
            t_orig, trans, desc, chef = get_full_video_data(v_url)
            res = generate_smart_recipe(t_orig, chef, trans, desc, c, ports, units)
            if res:
                st.session_state.recipe_result = res
                st.session_state.recipe_title = res.split('\n')[0].replace("TITLE:", "").strip()
                st.session_state.counter += 1
                update_global_counter()
                status.update(label=c['ui_ready'], state="complete")

if st.session_state.recipe_result:
    st.divider(); st.subheader(f"📖 {st.session_state.recipe_title}")
    st.markdown(st.session_state.recipe_result.replace("Check on Amazon", c['ui_buy']))
    
    pdf = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title)
    if pdf: 
        st.download_button(c['ui_dl'], data=pdf, file_name="Recipe.pdf", mime="application/pdf", use_container_width=True)

st.divider(); st.subheader(c['fb_header'])
with st.form("fb"):
    txt = st.text_area(c['fb_place']); mail = st.text_input(c['fb_mail'])
    if st.form_submit_button(c['fb_btn']):
        with open("user_feedback.txt", "a") as f: f.write(f"[{selected_lang}] {mail}: {txt}\n---\n")
        st.success(c['fb_thx'])
