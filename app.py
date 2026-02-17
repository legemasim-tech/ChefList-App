import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. INTERNATIONALE KONFIGURATION (VOLLSTÄNDIG FÜR 10 SPRACHEN) ---
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
    },
    "Español": {
        "tag": "cheflist21-20", "amz": "amazon.es", "curr": "EUR", "iso": "es",
        "btn_pay": "⚡ Apoyar ChefList Pro (0,90€)",
        "ui_header": "Convierte videos de YouTube en recetas PDF",
        "ui_input_label": "URL del video de YouTube:",
        "ui_servings": "Porciones:", "ui_units": "Sistema:", "ui_create": "Crear receta ✨",
        "ui_wait": "Calculando para {0} personas...", "ui_ready": "¡Listo!",
        "ui_dl": "📄 Descargar receta PDF", "ui_buy": "Comprar en Amazon*",
        "ui_counter_text": "Recetas creadas:",
        "ui_fb_header": "¡Ayúdanos a mejorar! 🍲", "ui_fb_btn": "Enviar ✨",
        "ui_fb_placeholder": "¿Cómo podemos mejorar?", "ui_fb_mail": "Correo (opcional)", "ui_fb_success": "¡Gracias! 🙌",
        "legal_title": "Info Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contacto:** legemasim@gmail.com",
        "legal_total": "Total de recetas:", "legal_amz": "✨ Socio de Amazon.", "legal_privacy_title": "🛡️ Privacidad",
        "legal_privacy_body": "No guardamos datos.", "legal_note": "⚠️ La IA puede cometer errores.", "admin_label": "🔑 Admin"
    },
    "Français": {
        "tag": "cheflist21-20", "amz": "amazon.fr", "curr": "EUR", "iso": "fr",
        "btn_pay": "⚡ Soutenir ChefList Pro (0,90€)",
        "ui_header": "Convertir YouTube en PDF imprimable",
        "ui_input_label": "URL de la vidéo YouTube:",
        "ui_servings": "Portions:", "ui_units": "Unités:", "ui_create": "Créer la recette ✨",
        "ui_wait": "Calcul pour {0} personnes...", "ui_ready": "Prêt!",
        "ui_dl": "📄 Télécharger le PDF", "ui_buy": "Acheter sur Amazon*",
        "ui_counter_text": "Recettes créées:",
        "ui_fb_header": "Aidez-nous! 🍲", "ui_fb_btn": "Envoyer ✨",
        "ui_fb_placeholder": "Comment s'améliorer?", "ui_fb_mail": "Email (optionnel)", "ui_fb_success": "Merci! 🙌",
        "legal_title": "Mentions Légales", "legal_op": "**Opérateur:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Total recettes:", "legal_amz": "✨ Partenaire Amazon.", "legal_privacy_title": "🛡️ Confidentialité",
        "legal_privacy_body": "Pas de stockage de données.", "legal_note": "⚠️ L'IA peut faire des erreurs.", "admin_label": "🔑 Admin"
    },
    "Italiano": {
        "tag": "cheflist21-20", "amz": "amazon.it", "curr": "EUR", "iso": "it",
        "btn_pay": "⚡ Sostieni ChefList Pro (0,90€)",
        "ui_header": "Trasforma YouTube in PDF stampabili",
        "ui_input_label": "URL del video YouTube:",
        "ui_servings": "Porzioni:", "ui_units": "Unità:", "ui_create": "Crea ricetta ✨",
        "ui_wait": "Calcolo per {0} persone...", "ui_ready": "Pronto!",
        "ui_dl": "📄 Scarica la ricetta PDF", "ui_buy": "Acquista su Amazon*",
        "ui_counter_text": "Ricette create:",
        "ui_fb_header": "Aiutaci a migliorare! 🍲", "ui_fb_btn": "Invia ✨",
        "ui_fb_placeholder": "Come possiamo migliorare?", "ui_fb_mail": "Email (opzionale)", "ui_fb_success": "Grazie! 🙌",
        "legal_title": "Info Legali", "legal_op": "**Operatore:** Markus Simmel", "legal_contact": "**Contatto:** legemasim@gmail.com",
        "legal_total": "Ricette totali:", "legal_amz": "✨ Partner Amazon.", "legal_privacy_title": "🛡️ Privacy",
        "legal_privacy_body": "Dati protetti.", "legal_note": "⚠️ L'IA può sbagliare.", "admin_label": "🔑 Admin"
    },
    "Português": {
        "tag": "cheflist21-20", "amz": "amazon.com.br", "curr": "BRL", "iso": "pt",
        "btn_pay": "⚡ Apoiar ChefList Pro (R$4,50)",
        "ui_header": "Transforme YouTube em PDFs",
        "ui_input_label": "URL do vídeo do YouTube:",
        "ui_servings": "Porções:", "ui_units": "Unidades:", "ui_create": "Criar receita ✨",
        "ui_wait": "Calculando para {0} pessoas...", "ui_ready": "Pronto!",
        "ui_dl": "📄 Baixar receita em PDF", "ui_buy": "Comprar na Amazon*",
        "ui_counter_text": "Receitas criadas:",
        "ui_fb_header": "Ajude-nos a melhorar! 🍲", "ui_fb_btn": "Enviar ✨",
        "ui_fb_placeholder": "Como podemos melhorar?", "ui_fb_mail": "E-mail", "ui_fb_success": "Obrigado! 🙌",
        "legal_title": "Info Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contato:** legemasim@gmail.com",
        "legal_total": "Total de receitas:", "legal_amz": "✨ Associado Amazon.", "legal_privacy_title": "🛡️ Privacidade",
        "legal_privacy_body": "Dados seguros.", "legal_note": "⚠️ IA pode errar.", "admin_label": "🔑 Admin"
    },
    "Nederlands": {
        "tag": "cheflist21-20", "amz": "amazon.nl", "curr": "EUR", "iso": "nl",
        "btn_pay": "⚡ Steun ChefList Pro (0,90€)",
        "ui_header": "YouTube naar PDF recepten",
        "ui_input_label": "YouTube-video-URL:",
        "ui_servings": "Porties:", "ui_units": "Eenheden:", "ui_create": "Recept maken ✨",
        "ui_wait": "Berekenen voor {0} porties...", "ui_ready": "Klaar!",
        "ui_dl": "📄 PDF downloaden", "ui_buy": "Koop op Amazon*",
        "ui_counter_text": "Recepten gemaakt:",
        "ui_fb_header": "Help ons verbeteren! 🍲", "ui_fb_btn": "Verzenden ✨",
        "ui_fb_placeholder": "Ideeën of fouten?", "ui_fb_mail": "E-mail", "ui_fb_success": "Bedankt! 🙌",
        "legal_title": "Info & Juridisch", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Totaal aantal:", "legal_amz": "✨ Amazon Partner.", "legal_privacy_title": "🛡️ Privacy",
        "legal_privacy_body": "Geen dataopslag.", "legal_note": "⚠️ AI kan fouten maken.", "admin_label": "🔑 Admin"
    },
    "Polski": {
        "tag": "cheflist21-20", "amz": "amazon.pl", "curr": "PLN", "iso": "pl",
        "btn_pay": "⚡ Wesprzyj ChefList Pro (4 PLN)",
        "ui_header": "Zmień YouTube w przepisy PDF",
        "ui_input_label": "URL filmu z YouTube:",
        "ui_servings": "Porcje:", "ui_units": "Jednostki:", "ui_create": "Utwórz przepis ✨",
        "ui_wait": "Obliczanie dla {0} osób...", "ui_ready": "Gotowe!",
        "ui_dl": "📄 Pobierz przepis PDF", "ui_buy": "Kup na Amazon*",
        "ui_counter_text": "Przepisy utworzone:",
        "ui_fb_header": "Pomóż nam się doskonalić! 🍲", "ui_fb_btn": "Wyślij ✨",
        "ui_fb_placeholder": "Co możemy poprawić?", "ui_fb_mail": "E-mail", "ui_fb_success": "Dziękujemy! 🙌",
        "legal_title": "Info Prawne", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Kontakt:** legemasim@gmail.com",
        "legal_total": "Suma przepisów:", "legal_amz": "✨ Partner Amazon.", "legal_privacy_title": "🛡️ Prywatność",
        "legal_privacy_body": "Dane są szyfrowane.", "legal_note": "⚠️ AI może się mylić.", "admin_label": "🔑 Admin"
    },
    "Türkçe": {
        "tag": "cheflist21-20", "amz": "amazon.com.tr", "curr": "TRY", "iso": "tr",
        "btn_pay": "⚡ Destek ChefList Pro (30 TL)",
        "ui_header": "YouTube videolarını PDF yapın",
        "ui_input_label": "YouTube Video URL'si:",
        "ui_servings": "Porsiyon:", "ui_units": "Birimler:", "ui_create": "Tarif oluştur ✨",
        "ui_wait": "{0} kişilik tarif hesaplanıyor...", "ui_ready": "Hazır!",
        "ui_dl": "📄 PDF İndir", "ui_buy": "Amazon'dan satın al*",
        "ui_counter_text": "Oluşturulan tarifler:",
        "ui_fb_header": "Bize yardım edin! 🍲", "ui_fb_btn": "Gönder ✨",
        "ui_fb_placeholder": "Fikirleriniz?", "ui_fb_mail": "E-posta", "ui_fb_success": "Teşekkürler! 🙌",
        "legal_title": "Yasal Bilgi", "legal_op": "**Operatör:** Markus Simmel", "legal_contact": "**İletişim:** legemasim@gmail.com",
        "legal_total": "Toplam tarif:", "legal_amz": "✨ Amazon Ortağı.", "legal_privacy_title": "🛡️ Veri Koruma",
        "legal_privacy_body": "Veriler şifrelenmiştir.", "legal_note": "⚠️ Yapay zeka hata yapabilir.", "admin_label": "🔑 Admin"
    },
    "日本語": {
        "tag": "cheflist21-20", "amz": "amazon.co.jp", "curr": "JPY", "iso": "ja",
        "btn_pay": "⚡ 支援 ChefList Pro (¥140)",
        "ui_header": "YouTube動画を印刷用PDFに変換",
        "ui_input_label": "YouTube動画のURL:",
        "ui_servings": "人数:", "ui_units": "単位:", "ui_create": "レシピを作成 ✨",
        "ui_wait": "{0}人分のレシピを計算中...", "ui_ready": "完了！",
        "ui_dl": "📄 PDFレシピをダウンロード", "ui_buy": "Amazonで購入*",
        "ui_counter_text": "作成済みレシピ数:",
        "ui_fb_header": "改善にご協力ください！ 🍲", "ui_fb_btn": "送信 ✨",
        "ui_fb_placeholder": "ご意見をお聞かせください", "ui_fb_mail": "メールアドレス", "ui_fb_success": "ありがとうございます！ 🙌",
        "legal_title": "法的情報", "legal_op": "**運営者:** Markus Simmel", "legal_contact": "**連絡先:** legemasim@gmail.com",
        "legal_total": "累計レシピ数:", "legal_amz": "✨ Amazonアソシエイト。", "legal_privacy_title": "🛡️ データ保護",
        "legal_privacy_body": "データは暗号化されます。", "legal_note": "⚠️ AIは間違いを犯す可能性があります。", "admin_label": "🔑 管理者"
    }
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
            with open(file_path, "r") as f: return int(f.read()) + base_value
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
    except:
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
st.markdown("<style>.stButton>button { font-size: 13px !important; } [data-testid='stSidebar'] img { background-color: white; padding: 10px; border-radius: 12px; border: 2px solid #e0e0e0; margin-bottom: 20px; }</style>", unsafe_allow_html=True)

# Session State Initialisierung
if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

# Automatische Spracherkennung (Einmalig beim Start)
if "user_lang_selection" not in st.session_state:
    try:
        accept_lang = st.context.headers.get("Accept-Language", "en")
        detected = accept_lang.split(",")[0].split("-")[0].lower()
        st.session_state.user_lang_selection = next((name for name, cfg in LANG_CONFIG.items() if cfg["iso"] == detected), "English")
    except:
        st.session_state.user_lang_selection = "English"

with st.sidebar:
    selected_language = st.selectbox("🌍 Language", list(LANG_CONFIG.keys()), index=list(LANG_CONFIG.keys()).index(st.session_state.user_lang_selection))
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
            admin_pw = st.text_input("Password", type="password", key="admin_pw_key_global")
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
            t_orig, trans, desc, chef = get_full_video_data(v_url)
            if trans or desc:
                res = generate_smart_recipe(t_orig, chef, trans, desc, c, ports, units, selected_language)
                if res:
                    st.session_state.recipe_result = res
                    st.session_state.recipe_title = t_orig
                    st.session_state.counter += 1
                    update_global_counter()
                    status.update(label=c['ui_ready'], state="complete", expanded=False)
                else: st.error("AI Error.")
            else: st.error("No data found for this video.")

if st.session_state.recipe_result:
    st.divider()
    st.subheader(f"📖 {st.session_state.get('recipe_title', 'Recipe')}")
    st.markdown(st.session_state.recipe_result.replace("Check on Amazon", c['ui_buy']))
    
    pdf_bytes = create_pdf(st.session_state.recipe_result, st.session_state.get("recipe_title", "Recipe"))
    if pdf_bytes:
        st.download_button(c['ui_dl'], pdf_bytes, file_name="Recipe.pdf", mime="application/pdf", use_container_width=True)

# --- FEEDBACK ---
st.divider()
st.subheader(c['ui_fb_header'])
with st.form("fb_form_global"):
    fb_text = st.text_area(c['ui_fb_placeholder'])
    fb_mail = st.text_input(c['ui_fb_mail'])
    if st.form_submit_button(c['ui_fb_btn']):
        if fb_text:
            with open("user_feedback.txt", "a") as f:
                f.write(f"[{selected_language}] {fb_mail}: {fb_text}\n---\n")
            st.success(c['ui_fb_success'])
