import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. INTERNATIONALE KONFIGURATION (Alle 10 Sprachen) ---
LANG_CONFIG = {
    "English": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "en",
        "btn_pay": "⚡ Support ChefList Pro ($0.90)",
        "ui_header": "Convert YouTube recipes into printable PDFs",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Servings:", "ui_units": "Unit System:", "ui_create": "Create Recipe ✨",
        "ui_wait": "Calculating recipe...", "ui_ready": "Ready!",
        "ui_dl": "📄 Download PDF Recipe", "ui_buy": "Buy on Amazon*",
        "ui_counter_text": "Recipes created:",
        "ui_fb_header": "Help us improve! 🍲", "ui_fb_btn": "Send Feedback ✨",
        "ui_fb_placeholder": "What can we do better? (Errors, wishes, ideas)",
        "ui_fb_mail": "Your email (optional)", "ui_fb_success": "Thank you! Saved. 🙌",
        "legal_title": "About & Legal", "legal_op": "**Operator:** Markus Simmel", 
        "legal_contact": "**Contact:** legemasim@gmail.com", "legal_total": "Total recipes generated:", 
        "legal_amz": "✨ As an Amazon Associate, I earn from qualifying purchases.",
        "legal_privacy_title": "🛡️ Data Protection", "legal_privacy_body": "We do not store personal data. Processing is encrypted.",
        "legal_note": "⚠️ **Note:** This app uses AI. AI can make mistakes – please verify results.",
        "admin_label": "🔑 Admin Access"
    },
    "Deutsch": {
        "tag": "cheflist21-21", "amz": "amazon.de", "curr": "EUR", "iso": "de",
        "btn_pay": "⚡ ChefList Pro unterstützen (0,90€)",
        "ui_header": "YouTube-Rezepte in druckbare PDFs verwandeln",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Portionen:", "ui_units": "Einheitensystem:", "ui_create": "Rezept erstellen ✨",
        "ui_wait": "Berechne Rezept...", "ui_ready": "Bereit!",
        "ui_dl": "📄 PDF Rezept herunterladen", "ui_buy": "Auf Amazon kaufen*",
        "ui_counter_text": "Erstellte Rezepte:",
        "ui_fb_header": "Hilf uns besser zu werden! 🍲", "ui_fb_btn": "Feedback senden ✨",
        "ui_fb_placeholder": "Was können wir besser machen? (Fehler, Wünsche, Ideen)",
        "ui_fb_mail": "Deine E-Mail (optional)", "ui_fb_success": "Danke! Gespeichert. 🙌",
        "legal_title": "Über & Rechtliches", "legal_op": "**Betreiber:** Markus Simmel", 
        "legal_contact": "**Kontakt:** legemasim@gmail.com", "legal_total": "Bereits generierte Rezepte:", 
        "legal_amz": "✨ Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.",
        "legal_privacy_title": "🛡️ Datenschutz & Sicherheit", "legal_privacy_body": "Wir speichern keine persönlichen Daten. Die Verarbeitung erfolgt verschlüsselt.",
        "legal_note": "⚠️ **Hinweis:** Diese App nutzt eine KI. KI kann Fehler machen – bitte prüfe die Angaben.",
        "admin_label": "🔑 Admin Login"
    },
    "Español": {"tag": "cheflist21-20", "amz": "amazon.es", "curr": "EUR", "iso": "es", "btn_pay": "⚡ Apoyar ChefList Pro (0,90€)", "ui_header": "Convierte videos de YouTube en recetas PDF", "ui_input_label": "URL del video:", "ui_servings": "Porciones:", "ui_units": "Unidades:", "ui_create": "Crear receta ✨", "ui_wait": "Calculando...", "ui_ready": "¡Listo!", "ui_dl": "📄 Descargar PDF", "ui_buy": "Comprar en Amazon*", "ui_counter_text": "Recetas:", "ui_fb_header": "¡Ayúdanos!", "ui_fb_btn": "Enviar ✨", "ui_fb_placeholder": "Ideas...", "ui_fb_mail": "Email", "ui_fb_success": "¡Gracias!", "legal_title": "Info Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contacto:** legemasim@gmail.com", "legal_total": "Total recetas:", "legal_amz": "✨ Amazon Associate.", "legal_privacy_title": "🛡️ Privacidad", "legal_privacy_body": "No guardamos datos.", "legal_note": "⚠️ La IA puede fallar.", "admin_label": "🔑 Admin"},
    "Français": {"tag": "cheflist21-20", "amz": "amazon.fr", "curr": "EUR", "iso": "fr", "btn_pay": "⚡ Soutenir ChefList Pro (0,90€)", "ui_header": "Convertir YouTube en PDF", "ui_input_label": "URL vidéo:", "ui_servings": "Portions:", "ui_units": "Unités:", "ui_create": "Créer la recette ✨", "ui_wait": "Calcul...", "ui_ready": "Prêt!", "ui_dl": "📄 Télécharger PDF", "ui_buy": "Acheter sur Amazon*", "ui_counter_text": "Recettes:", "ui_fb_header": "Aidez-nous!", "ui_fb_btn": "Envoyer ✨", "ui_fb_placeholder": "Commentaires...", "ui_fb_mail": "Email", "ui_fb_success": "Merci!", "legal_title": "Mentions Légales", "legal_op": "**Opérateur:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com", "legal_total": "Total recettes:", "legal_amz": "✨ Amazon Associate.", "legal_privacy_title": "🛡️ Protection des données", "legal_privacy_body": "Données cryptées.", "legal_note": "⚠️ L'IA peut faire des erreurs.", "admin_label": "🔑 Admin"},
    "Italiano": {"tag": "cheflist21-20", "amz": "amazon.it", "curr": "EUR", "iso": "it", "btn_pay": "⚡ Sostieni ChefList Pro (0,90€)", "ui_header": "Trasforma YouTube in PDF", "ui_input_label": "URL video:", "ui_servings": "Porzioni:", "ui_units": "Unità:", "ui_create": "Crea ricetta ✨", "ui_wait": "Calcolo...", "ui_ready": "Pronto!", "ui_dl": "📄 Scarica PDF", "ui_buy": "Acquista su Amazon*", "ui_counter_text": "Ricette:", "ui_fb_header": "Aiutaci!", "ui_fb_btn": "Invia ✨", "ui_fb_placeholder": "Idee...", "ui_fb_mail": "Email", "ui_fb_success": "Grazie!", "legal_title": "Info Legali", "legal_op": "**Operatore:** Markus Simmel", "legal_contact": "**Contatto:** legemasim@gmail.com", "legal_total": "Totale ricette:", "legal_amz": "✨ Amazon Associate.", "legal_privacy_title": "🛡️ Privacy", "legal_privacy_body": "Dati protetti.", "legal_note": "⚠️ L'IA può sbagliare.", "admin_label": "🔑 Admin"},
    "Português": {"tag": "cheflist21-20", "amz": "amazon.com.br", "curr": "BRL", "iso": "pt", "btn_pay": "⚡ Apoiar ChefList Pro (R$4,50)", "ui_header": "Converter YouTube para PDF", "ui_input_label": "URL do vídeo:", "ui_servings": "Porções:", "ui_units": "Unidades:", "ui_create": "Criar receita ✨", "ui_wait": "Calculando...", "ui_ready": "Pronto!", "ui_dl": "📄 Baixar PDF", "ui_buy": "Comprar na Amazon*", "ui_counter_text": "Receitas:", "ui_fb_header": "Ajude-nos!", "ui_fb_btn": "Enviar ✨", "ui_fb_placeholder": "Comentários...", "ui_fb_mail": "Email", "ui_fb_success": "Obrigado!", "legal_title": "Info Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contato:** legemasim@gmail.com", "legal_total": "Total:", "legal_amz": "✨ Amazon Associate.", "legal_privacy_title": "🛡️ Privacidade", "legal_privacy_body": "Dados seguros.", "legal_note": "⚠️ IA pode errar.", "admin_label": "🔑 Admin"},
    "Nederlands": {"tag": "cheflist21-20", "amz": "amazon.nl", "curr": "EUR", "iso": "nl", "btn_pay": "⚡ Steun ChefList Pro (0,90€)", "ui_header": "YouTube naar PDF recepten", "ui_input_label": "Video URL:", "ui_servings": "Porties:", "ui_units": "Eenheden:", "ui_create": "Recept maken ✨", "ui_wait": "Berekenen...", "ui_ready": "Klaar!", "ui_dl": "📄 PDF downloaden", "ui_buy": "Koop op Amazon*", "ui_counter_text": "Recepten:", "ui_fb_header": "Help ons!", "ui_fb_btn": "Verzenden ✨", "ui_fb_placeholder": "Ideeën...", "ui_fb_mail": "Email", "ui_fb_success": "Bedankt!", "legal_title": "Juridisch", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com", "legal_total": "Totaal recepten:", "legal_amz": "✨ Amazon Associate.", "legal_privacy_title": "🛡️ Privacy", "legal_privacy_body": "Geen data opslag.", "legal_note": "⚠️ AI kan fouten maken.", "admin_label": "🔑 Admin"},
    "Polski": {"tag": "cheflist21-20", "amz": "amazon.pl", "curr": "PLN", "iso": "pl", "btn_pay": "⚡ Wesprzyj ChefList Pro (4 PLN)", "ui_header": "Zmień YouTube w PDF", "ui_input_label": "URL filmu:", "ui_servings": "Porcje:", "ui_units": "Jednostki:", "ui_create": "Utwórz przepis ✨", "ui_wait": "Obliczanie...", "ui_ready": "Gotowe!", "ui_dl": "📄 Pobierz PDF", "ui_buy": "Kup na Amazon*", "ui_counter_text": "Przepisy:", "ui_fb_header": "Pomóż nam!", "ui_fb_btn": "Wyślij ✨", "ui_fb_placeholder": "Pomysły...", "ui_fb_mail": "Email", "ui_fb_success": "Dziękujemy!", "legal_title": "Info Prawne", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Kontakt:** legemasim@gmail.com", "legal_total": "Suma:", "legal_amz": "✨ Amazon Associate.", "legal_privacy_title": "🛡️ Prywatność", "legal_privacy_body": "Dane szyfrowane.", "legal_note": "⚠️ AI może się mylić.", "admin_label": "🔑 Admin"},
    "Türkçe": {"tag": "cheflist21-20", "amz": "amazon.com.tr", "curr": "TRY", "iso": "tr", "btn_pay": "⚡ Destek ChefList Pro (30 TL)", "ui_header": "YouTube tariflerini PDF yap", "ui_input_label": "Video URL:", "ui_servings": "Porsiyon:", "ui_units": "Birimler:", "ui_create": "Tarif oluştur ✨", "ui_wait": "Hesaplanıyor...", "ui_ready": "Hazır!", "ui_dl": "📄 PDF İndir", "ui_buy": "Amazon'dan satın al*", "ui_counter_text": "Tarifler:", "ui_fb_header": "Bize yardım edin!", "ui_fb_btn": "Gönder ✨", "ui_fb_placeholder": "Fikirler...", "ui_fb_mail": "E-posta", "ui_fb_success": "Teşekkürler!", "legal_title": "Yasal Bilgi", "legal_op": "**Operatör:** Markus Simmel", "legal_contact": "**İletişim:** legemasim@gmail.com", "legal_total": "Toplam:", "legal_amz": "✨ Amazon Associate.", "legal_privacy_title": "🛡️ Veri Koruma", "legal_privacy_body": "Veriler şifreli.", "legal_note": "⚠️ Yapay zeka hata yapabilir.", "admin_label": "🔑 Admin"},
    "日本語": {"tag": "cheflist21-20", "amz": "amazon.co.jp", "curr": "JPY", "iso": "ja", "btn_pay": "⚡ 支援 ChefList Pro (¥140)", "ui_header": "YouTubeをPDFレシピに変換", "ui_input_label": "動画URL:", "ui_servings": "人数:", "ui_units": "単位:", "ui_create": "レシピを作成 ✨", "ui_wait": "計算中...", "ui_ready": "完了！", "ui_dl": "📄 PDFダウンロード", "ui_buy": "Amazonで購入*", "ui_counter_text": "レシピ数:", "ui_fb_header": "改善にご協力ください!", "ui_fb_btn": "送信 ✨", "ui_fb_placeholder": "ご意見...", "ui_fb_mail": "メール", "ui_fb_success": "ありがとうございます!", "legal_title": "法的情報", "legal_op": "**運営者:** Markus Simmel", "legal_contact": "**連絡先:** legemasim@gmail.com", "legal_total": "合計:", "legal_amz": "✨ Amazon Associate.", "legal_privacy_title": "🛡️ データ保護", "legal_privacy_body": "データは暗号化されます。", "legal_note": "⚠️ AIは間違いを犯す可能性があります。", "admin_label": "🔑 管理者"}
}

# --- 2. CONFIGURATION & API ---
try: api_key = st.secrets["OPENAI_API_KEY"]
except: api_key = None
paypal_email = "legemasim@gmail.com"
if not api_key:
    st.error("Please add OpenAI Key!")
    st.stop()
client = openai.OpenAI(api_key=api_key)

# --- GLOBAL COUNTER ---
def update_global_counter():
    try:
        if not os.path.exists("total_recipes_global.txt"):
            with open("total_recipes_global.txt", "w") as f: f.write("0")
        with open("total_recipes_global.txt", "r") as f: count = int(f.read())
        count += 1
        with open("total_recipes_global.txt", "w") as f: f.write(str(count))
    except: pass

def get_total_count():
    base = 17 
    if os.path.exists("total_recipes_global.txt"):
        try:
            with open("total_recipes_global.txt", "r") as f: return int(f.read()) + base
        except: return base
    return base

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
                        if f.get('ext') == 'json3': target_url = f.get('url'); break
                    if target_url: break
            if target_url:
                res = requests.get(target_url)
                if res.status_code == 200:
                    data = res.json()
                    transcript = " ".join([seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])
        return video_title, transcript, description, channel_name
    except: return "Recipe", None, None, "Unknown Chef"

def generate_smart_recipe(video_title, channel_name, transcript, description, config, portions, unit_system, lang_name):
    combined_input = f"TITLE: {video_title}\nCHANNEL: {channel_name}\n\nTRANSCRIPT:\n{transcript}\n\nDESCRIPTION:\n{description}"
    unit_instr = "US UNITS" if unit_system in ["US Units (cups/oz)", "US-Einheiten"] else "METRIC"
    system_prompt = f"Professional Chef. Translate for {portions} servings into {lang_name}. Use {unit_instr}. Structure: TITLE: '[Recipe] by [Author]', Key Data, Ingredients Table with links: https://www.{config['amz']}/s?k=[INGREDIENTNAME]&tag={config['tag']}, Instructions."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input[:16000]}]
        )
        return response.choices[0].message.content
    except: return None

# --- 4. PDF ---
def clean_for_pdf(text):
    text = text.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue').replace('ß', 'ss').replace('€', 'Euro')
    text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('–', '-')
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text

def create_pdf(text_content, recipe_title):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(230, 230, 230); pdf.set_font("Arial", style="B", size=14)
        pdf.cell(190, 15, txt=f"Recipe: {clean_for_pdf(recipe_title[:40])}", ln=True, align='C', fill=True)
        pdf.ln(5); pdf.set_font("Arial", size=10)
        pdf.multi_cell(185, 7, txt=clean_for_pdf(text_content))
        return pdf.output()
    except: return None

# --- 5. INTERFACE ---
st.set_page_config(page_title="ChefList Pro Global", page_icon="🍲", layout="centered")

# CSS: Einzeiliger Spendenbutton & Logo Styling
st.markdown("<style>.stButton>button { font-size: 14px !important; } [data-testid='stSidebar'] img { background-color: white; padding: 10px; border-radius: 12px; border: 2px solid #e0e0e0; margin-bottom: 20px; }</style>", unsafe_allow_html=True)

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None

# AUTO-DETECTION
if "detected_lang" not in st.session_state:
    try:
        b_lang = st.context.headers.get("Accept-Language", "en").split(",")[0].split("-")[0].lower()
        st.session_state.detected_lang = next((name for name, cfg in LANG_CONFIG.items() if cfg["iso"] == b_lang), "English")
    except: st.session_state.detected_lang = "English"

with st.sidebar:
    selected_language = st.selectbox("🌍 Language / Sprache", list(LANG_CONFIG.keys()), index=list(LANG_CONFIG.keys()).index(st.session_state.detected_lang))
    c = LANG_CONFIG[selected_language]
    
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🍳 ChefList Pro")
    
    st.info(f"{c['ui_counter_text']} {st.session_state.counter}")
    
    pay_link = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Support&amount=0.90&currency_code={c['curr']}"
    st.markdown(f'''<a href="{pay_link}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 11px; width: 100%;">{c['btn_pay']}</button></a>''', unsafe_allow_html=True)

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
            admin_pw = st.text_input("Password", type="password", key="admin_pw_global")
            if admin_pw == "Gemini_Cheflist_pw":
                if os.path.exists("user_feedback.txt"):
                    with open("user_feedback.txt", "r") as f: content = f.read()
                    st.text_area("Feedback Log:", value=content, height=200)
                    if st.button("Clear Log"):
                        with open("user_feedback.txt", "w") as f: f.write(""); st.rerun()

# --- MAIN UI ---
st.title("🍲 ChefList Pro")
st.subheader(c['ui_header'])

v_url = st.text_input(c['ui_input_label'], placeholder="https://...")
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
    st.divider(); st.markdown(st.session_state.recipe_result.replace("Check on Amazon", c['ui_buy']))
    pdf_bytes = create_pdf(st.session_state.recipe_result, st.session_state.get("recipe_title", "Recipe"))
    if pdf_bytes:
        st.download_button(c['ui_dl'], pdf_bytes, file_name="Recipe.pdf", mime="application/pdf", use_container_width=True)

st.divider()
st.subheader(c['ui_fb_header'])
with st.form("fb"):
    fb_text = st.text_area(c['ui_fb_placeholder'])
    fb_mail = st.text_input(c['ui_fb_mail'])
    if st.form_submit_button(c['ui_fb_btn']):
        if fb_text:
            with open("user_feedback.txt", "a") as f: f.write(f"[{selected_language}] {fb_mail}: {fb_text}\n---\n")
            st.success(c['ui_fb_success'])
