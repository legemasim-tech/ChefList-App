import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. INTERNATIONALE KONFIGURATION ---
# Hier sind alle 10 Sprachen mit ihren spezifischen Texten hinterlegt
LANG_CONFIG = {
    "English": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "en",
        "ui_header": "Convert YouTube recipes into printable PDFs",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Servings:", "ui_units": "Unit System:", "ui_create": "Create Recipe ✨",
        "ui_wait": "Calculating recipe for {0} servings...", "ui_ready": "Ready!",
        "ui_btn_pay": "⚡ Support ChefList Pro ($0.90)", "ui_dl": "📄 Download PDF Recipe",
        "ui_counter_text": "Recipes created:", "ui_fb_header": "Help us improve! 🍲",
        "ui_fb_btn": "Send Feedback ✨", "ui_fb_placeholder": "What can we do better?",
        "ui_fb_mail": "Your email (optional)", "ui_fb_success": "Thank you! Saved. 🙌",
        "legal_title": "About & Legal", "legal_op": "**Operator:** Markus Simmel", 
        "legal_contact": "**Contact:** legemasim@gmail.com", "legal_total": "Total recipes generated:", 
        "legal_amz": "✨ As an Amazon Associate, I earn from qualifying purchases.",
        "legal_privacy_title": "🛡️ Data Protection", "legal_privacy_body": "We do not store personal data. Processing is encrypted.",
        "legal_note": "⚠️ **Note:** AI can make mistakes – please verify cooking times.",
        "ai_lang": "ENGLISH", "pdf_recipe": "Recipe", "pdf_instr": "Instructions", "pdf_enjoy": "Enjoy your meal!"
    },
    "Deutsch": {
        "tag": "cheflist21-21", "amz": "amazon.de", "curr": "EUR", "iso": "de",
        "ui_header": "YouTube-Rezepte in druckbare PDFs verwandeln",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Portionen:", "ui_units": "Einheitensystem:", "ui_create": "Rezept erstellen ✨",
        "ui_wait": "Berechne Rezept für {0} Portionen...", "ui_ready": "Bereit!",
        "ui_btn_pay": "⚡ ChefList Pro unterstützen (0,90€)", "ui_dl": "📄 PDF Rezept herunterladen",
        "ui_counter_text": "Erstellte Rezepte:", "ui_fb_header": "Hilf uns besser zu werden! 🍲",
        "ui_fb_btn": "Feedback senden ✨", "ui_fb_placeholder": "Was können wir besser machen?",
        "ui_fb_mail": "Deine E-Mail (optional)", "ui_fb_success": "Danke! Gespeichert. 🙌",
        "legal_title": "Über & Rechtliches", "legal_op": "**Betreiber:** Markus Simmel", 
        "legal_contact": "**Kontakt:** legemasim@gmail.com", "legal_total": "Bereits generierte Rezepte:", 
        "legal_amz": "✨ Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.",
        "legal_privacy_title": "🛡️ Datenschutz & Sicherheit", "legal_privacy_body": "Wir speichern keine persönlichen Daten. Verschlüsselt.",
        "legal_note": "⚠️ **Hinweis:** KI kann Fehler machen – bitte prüfe die Angaben.",
        "ai_lang": "GERMAN", "pdf_recipe": "Rezept", "pdf_instr": "Zubereitung", "pdf_enjoy": "Guten Appetit!"
    },
    "Español": {
        "tag": "cheflist21-20", "amz": "amazon.es", "curr": "EUR", "iso": "es",
        "ui_header": "Convierte videos de YouTube en recetas PDF",
        "ui_input_label": "URL del video de YouTube:",
        "ui_servings": "Porciones:", "ui_units": "Sistema:", "ui_create": "Crear receta ✨",
        "ui_wait": "Calculando para {0} personas...", "ui_ready": "¡Listo!",
        "ui_btn_pay": "⚡ Apoyar ChefList Pro (0,90€)", "ui_dl": "📄 Descargar receta PDF",
        "ui_counter_text": "Recetas creadas:", "ui_fb_header": "¡Ayúdanos a mejorar! 🍲",
        "ui_fb_btn": "Enviar ✨", "ui_fb_placeholder": "¿Cómo podemos mejorar?",
        "ui_fb_mail": "Correo (opcional)", "ui_fb_success": "¡Gracias! Guardado. 🙌",
        "legal_title": "Info Legal", "legal_op": "**Operador:** Markus Simmel", 
        "legal_contact": "**Contacto:** legemasim@gmail.com", "legal_total": "Total de recetas:", 
        "legal_amz": "✨ Socio de Amazon.", "legal_privacy_title": "🛡️ Privacidad",
        "legal_privacy_body": "No guardamos datos.", "legal_note": "⚠️ La IA puede cometer errores.",
        "ai_lang": "SPANISH", "pdf_recipe": "Receta", "pdf_instr": "Instrucciones", "pdf_enjoy": "¡Buen provecho!"
    },
    "Français": {
        "tag": "cheflist21-20", "amz": "amazon.fr", "curr": "EUR", "iso": "fr",
        "ui_header": "YouTube en PDF imprimable",
        "ui_input_label": "URL de la vidéo YouTube:",
        "ui_servings": "Portions:", "ui_units": "Unités:", "ui_create": "Créer la recette ✨",
        "ui_wait": "Calcul pour {0} personnes...", "ui_ready": "Prêt!",
        "ui_btn_pay": "⚡ Soutenir ChefList Pro (0,90€)", "ui_dl": "📄 Télécharger le PDF",
        "ui_counter_text": "Recettes créées:", "ui_fb_header": "Aidez-nous! 🍲",
        "ui_fb_btn": "Envoyer ✨", "ui_fb_placeholder": "Comment s'améliorer?",
        "ui_fb_mail": "Email (optionnel)", "ui_fb_success": "Merci! 🙌",
        "legal_title": "Mentions Légales", "legal_op": "**Opérateur:** Markus Simmel", 
        "legal_contact": "**Contact:** legemasim@gmail.com", "legal_total": "Total recettes:", 
        "legal_amz": "✨ Partenaire Amazon.", "legal_privacy_title": "🛡️ Confidentialité",
        "legal_privacy_body": "Pas de stockage.", "legal_note": "⚠️ L'IA peut faire des erreurs.",
        "ai_lang": "FRENCH", "pdf_recipe": "Recette", "pdf_instr": "Instructions", "pdf_enjoy": "Bon appétit!"
    },
    "Italiano": {
        "tag": "cheflist21-20", "amz": "amazon.it", "curr": "EUR", "iso": "it",
        "ui_header": "Trasforma YouTube in PDF",
        "ui_input_label": "URL del video YouTube:",
        "ui_servings": "Porzioni:", "ui_units": "Unità:", "ui_create": "Crea ricetta ✨",
        "ui_wait": "Calcolo per {0} persone...", "ui_ready": "Pronto!",
        "ui_btn_pay": "⚡ Sostieni ChefList Pro (0,90€)", "ui_dl": "📄 Scarica PDF",
        "ui_counter_text": "Ricette create:", "ui_fb_header": "Aiutaci! 🍲",
        "ui_fb_btn": "Invia ✨", "ui_fb_placeholder": "Idee?",
        "ui_fb_mail": "Email", "ui_fb_success": "Grazie! 🙌",
        "legal_title": "Info Legali", "legal_op": "**Operatore:** Markus Simmel", 
        "legal_contact": "legemasim@gmail.com", "legal_total": "Ricette totali:", 
        "legal_amz": "✨ Partner Amazon.", "legal_privacy_title": "🛡️ Privacy",
        "legal_privacy_body": "Dati protetti.", "legal_note": "⚠️ IA può sbagliare.",
        "ai_lang": "ITALIAN", "pdf_recipe": "Ricetta", "pdf_instr": "Istruzioni", "pdf_enjoy": "Buon appetito!"
    },
    "Português": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "pt",
        "ui_header": "YouTube para PDF", "ui_input_label": "URL do vídeo:",
        "ui_servings": "Porções:", "ui_units": "Unidades:", "ui_create": "Criar ✨",
        "ui_wait": "Calculando...", "ui_ready": "Pronto!",
        "ui_btn_pay": "⚡ Apoiar ChefList (0,90 USD)", "ui_dl": "📄 Baixar PDF",
        "ui_counter_text": "Receitas:", "ui_fb_header": "Ajude-nos!",
        "ui_fb_btn": "Enviar ✨", "ui_fb_placeholder": "Sugestões?",
        "ui_fb_mail": "Email", "ui_fb_success": "Obrigado! 🙌",
        "legal_title": "Info Legal", "legal_op": "Markus Simmel", "legal_total": "Total:",
        "legal_amz": "✨ Amazon.", "legal_privacy_title": "🛡️ Privacidade", "legal_privacy_body": "Seguro.",
        "legal_note": "⚠️ IA erro.", "ai_lang": "PORTUGUESE", "pdf_recipe": "Receita", 
        "pdf_instr": "Instruções", "pdf_enjoy": "Bom apetite!"
    },
    "Nederlands": {
        "tag": "cheflist21-20", "amz": "amazon.nl", "curr": "EUR", "iso": "nl",
        "ui_header": "YouTube naar PDF", "ui_input_label": "Video URL:",
        "ui_servings": "Porties:", "ui_units": "Eenheden:", "ui_create": "Maken ✨",
        "ui_wait": "Berekenen...", "ui_ready": "Klaar!",
        "ui_btn_pay": "⚡ Steun ChefList (0,90€)", "ui_dl": "📄 PDF downloaden",
        "ui_counter_text": "Recepten:", "ui_fb_header": "Help ons!",
        "ui_fb_btn": "Verzenden ✨", "ui_fb_placeholder": "Ideeën?",
        "ui_fb_mail": "Email", "ui_fb_success": "Bedankt! 🙌",
        "legal_title": "Juridisch", "legal_op": "Simmel", "legal_total": "Totaal:",
        "legal_amz": "✨ Amazon.", "legal_privacy_title": "🛡️ Privacy", "legal_privacy_body": "Geen data.",
        "legal_note": "⚠️ AI fout.", "ai_lang": "DUTCH", "pdf_recipe": "Recept", 
        "pdf_instr": "Instructions", "pdf_enjoy": "Eet smakelijk!"
    },
    "Polski": {
        "tag": "cheflist21-20", "amz": "amazon.pl", "curr": "PLN", "iso": "pl",
        "ui_header": "YouTube na PDF", "ui_input_label": "URL filmu:",
        "ui_servings": "Porcje:", "ui_units": "Jednostki:", "ui_create": "Utwórz ✨",
        "ui_wait": "Obliczanie...", "ui_ready": "Gotowe!",
        "ui_btn_pay": "⚡ Wesprzyj (4 PLN)", "ui_dl": "📄 Pobierz PDF",
        "ui_counter_text": "Przepisy:", "ui_fb_header": "Pomoc!",
        "ui_fb_btn": "Wyślij ✨", "ui_fb_placeholder": "Pomysły?",
        "ui_fb_mail": "Email", "ui_fb_success": "Dzięki! 🙌",
        "legal_title": "Prawne", "legal_op": "Simmel", "legal_total": "Suma:",
        "legal_amz": "✨ Amazon.", "legal_privacy_title": "🛡️ Prywatność", "legal_privacy_body": "Szyfrowane.",
        "legal_note": "⚠️ Błąd AI.", "ai_lang": "POLISH", "pdf_recipe": "Przepis", 
        "pdf_instr": "Instrukcje", "pdf_enjoy": "Smacznego!"
    },
    "Türkçe": {
        "tag": "cheflist21-20", "amz": "amazon.com.tr", "curr": "TRY", "iso": "tr",
        "ui_header": "YouTube'dan PDF'e", "ui_input_label": "Video URL'si:",
        "ui_servings": "Porsiyon:", "ui_units": "Birimler:", "ui_create": "Oluştur ✨",
        "ui_wait": "Hesaplanıyor...", "ui_ready": "Hazır!",
        "ui_btn_pay": "⚡ Destek (30 TL)", "ui_dl": "📄 PDF İndir",
        "ui_counter_text": "Tarifler:", "ui_fb_header": "Yardım!",
        "ui_fb_btn": "Gönder ✨", "ui_fb_placeholder": "Fikirler?",
        "ui_fb_mail": "E-posta", "ui_fb_success": "Teşekkürler! 🙌",
        "legal_title": "Yasal", "legal_op": "Simmel", "legal_total": "Toplam:",
        "legal_amz": "✨ Amazon.", "legal_privacy_title": "🛡️ Veri", "legal_privacy_body": "Şifreli.",
        "legal_note": "⚠️ AI hata.", "ai_lang": "TURKISH", "pdf_recipe": "Tarif", 
        "pdf_instr": "Talimatlar", "pdf_enjoy": "Afiyet olsun!"
    },
    "日本語": {
        "tag": "cheflist21-20", "amz": "amazon.co.jp", "curr": "JPY", "iso": "ja",
        "ui_header": "YouTubeをPDFに", "ui_input_label": "動画URL:",
        "ui_servings": "人数:", "ui_units": "単位:", "ui_create": "作成 ✨",
        "ui_wait": "計算中...", "ui_ready": "完了！",
        "ui_btn_pay": "⚡ 支援 (¥140)", "ui_dl": "📄 PDF保存",
        "ui_counter_text": "レシピ数:", "ui_fb_header": "改善にご協力ください",
        "ui_fb_btn": "送信 ✨", "ui_fb_placeholder": "ご意見は?",
        "ui_fb_mail": "メール", "ui_fb_success": "感謝! 🙌",
        "legal_title": "法的情報", "legal_op": "Simmel", "legal_total": "累計:",
        "legal_amz": "✨ Amazon.", "legal_privacy_title": "🛡️ 保護", "legal_privacy_body": "安全.",
        "legal_note": "⚠️ AIミス.", "ai_lang": "JAPANESE", "pdf_recipe": "レシピ", 
        "pdf_instr": "作り方", "pdf_enjoy": "召し上がれ！"
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
        channel_name = info.get('uploader', 'Chef')
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
        return "Recipe", None, None, "Chef"

def generate_smart_recipe(video_title, channel_name, transcript, description, config, portions, unit_system):
    combined_input = f"ORIGINAL TITLE: {video_title}\nSOURCE: {channel_name}\n\nTRANSCRIPT:\n{transcript}\n\nDESCRIPTION:\n{description}"
    unit_instruction = "US UNITS" if unit_system.startswith("US") else "METRIC (g, ml)"
    
    system_prompt = f"""
    You are a professional chef. 
    TASK: Translate and calculate this recipe into {config['ai_lang']}.
    
    RULES:
    1. The ENTIRE response (Title, Headers, Labels, Instructions) must be in {config['ai_lang']}.
    2. Recalculate quantities for exactly {portions} person(s). 
    3. Use {unit_instruction}.
    4. Format the START exactly like this: "TITLE: [Translated Recipe Name] by [Author]"
    5. Table columns: Amount | Ingredient | Shop (https://www.{config['amz']}/s?k=[INGREDIENT]&tag={config['tag']})
    6. Link text (e.g., 'Buy on Amazon') must be in {config['ai_lang']}.
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
    for char, rep in replacements.items(): text = text.replace(char, rep)
    text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('–', '-')
    # Entfernt alle nicht-ASCII Zeichen für FPDF Stabilität
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text

def create_pdf(text_content, recipe_title, config):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", style="B", size=14)
        title = clean_for_pdf(recipe_title[:40])
        pdf.cell(190, 15, txt=f"{config['pdf_recipe']}: {title}", ln=True, align='C', fill=True)
        pdf.ln(5)
        pdf.set_font("Arial", size=10)
        
        lines = text_content.split('\n')
        for line in lines:
            line = clean_for_pdf(line.strip())
            if not line: continue
            if '|' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    pdf.cell(0, 8, txt=f"[ ] {parts[0]} {parts[1]}", ln=True)
            else:
                pdf.multi_cell(0, 7, txt=line)
        
        pdf.ln(10)
        pdf.set_font("Arial", style="I", size=10)
        pdf.cell(0, 10, txt=config['pdf_enjoy'], ln=True, align='C')
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    except: return None

# --- 5. INTERFACE ---
st.set_page_config(page_title="ChefList Pro Global", page_icon="🍲", layout="centered")

# Automatik Logik
if "user_lang_selection" not in st.session_state:
    try:
        lang_header = st.context.headers.get("Accept-Language", "en")
        primary_code = lang_header.split(",")[0].split("-")[0].lower()
        mapping = {"de": "Deutsch", "en": "English", "es": "Español", "fr": "Français", "it": "Italiano", "pt": "Português", "nl": "Nederlands", "pl": "Polski", "tr": "Türkçe", "ja": "日本語"}
        st.session_state.user_lang_selection = mapping.get(primary_code, "English")
    except:
        st.session_state.user_lang_selection = "English"

if "recipe_result_global" not in st.session_state: st.session_state.recipe_result_global = None

with st.sidebar:
    lang_options = list(LANG_CONFIG.keys())
    selected_lang = st.selectbox("🌍 Language", lang_options, index=lang_options.index(st.session_state.user_lang_selection))
    c = LANG_CONFIG[selected_lang]
    
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🍳 ChefList Pro")
    
    st.info(f"{c['ui_counter_text']} {get_total_count()}")
    
    pay_url = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Support&amount=0.90&currency_code={c['curr']}"
    st.markdown(f'''<a href="{pay_url}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 11px; width: 100%;">{c['ui_btn_pay']}</button></a>''', unsafe_allow_html=True)

    st.markdown("---")
    with st.expander(f"ℹ️ {c['legal_title']}"):
        st.caption(c["legal_op"]); st.caption(c["legal_contact"]); st.divider()
        st.caption(c["legal_amz"]); st.subheader(c["legal_privacy_title"]); st.caption(c["legal_privacy_body"])
        st.divider(); st.caption(c["legal_note"])

st.title("🍲 ChefList Pro")
st.subheader(c['ui_header'])

v_url = st.text_input(c['ui_input_label'], placeholder="https://...")
col1, col2 = st.columns(2)
ports = col1.slider(c['ui_servings'], 1, 10, 4)
units = col2.radio(c['ui_units'], list(LANG_CONFIG["English"]["ui_units_options"] if selected_lang == "English" else LANG_CONFIG["Deutsch"]["ui_units_options"] if selected_lang == "Deutsch" else ["US Units", "Metric"]), horizontal=True)

if st.button(c['ui_create'], use_container_width=True):
    if v_url:
        with st.status(c['ui_wait'].format(ports)) as status:
            t_orig, trans, desc, chef = get_full_video_data(v_url)
            res = generate_smart_recipe(t_orig, chef, trans, desc, c, ports, units)
            if res:
                st.session_state.recipe_result_global = res
                # Extrahiere übersetzten Titel
                try:
                    st.session_state.recipe_title_global = res.split('\n')[0].replace('TITLE:', '').strip()
                except:
                    st.session_state.recipe_title_global = t_orig
                update_global_counter()
                status.update(label=c['ui_ready'], state="complete")

if st.session_state.recipe_result_global:
    st.divider()
    st.subheader(f"📖 {st.session_state.get('recipe_title_global', 'Recipe')}")
    st.markdown(st.session_state.recipe_result_global)
    
    pdf_bytes = create_pdf(st.session_state.recipe_result_global, st.session_state.get('recipe_title_global', 'Recipe'), c)
    if pdf_bytes:
        st.download_button(c['ui_dl'], data=pdf_bytes, file_name="Recipe.pdf", mime="application/pdf", use_container_width=True)

# Feedback
st.divider()
st.subheader(c['ui_fb_header'])
with st.form("fb"):
    txt = st.text_area(c['ui_fb_placeholder']); mail = st.text_input(c['ui_fb_mail'])
    if st.form_submit_button(c['ui_fb_btn']):
        with open("user_feedback.txt", "a") as f: f.write(f"[{selected_lang}] {mail}: {txt}\n---\n")
        st.success(c['ui_fb_success'])
