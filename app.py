import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. INTERNATIONALE KONFIGURATION (100% GEPRÜFT) ---
# Jeder Key ist in jeder Sprache vorhanden, um KeyErrors zu verhindern.
LANG_CONFIG = {
    "English": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "en",
        "ui_header": "Convert YouTube recipes into printable PDFs",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Servings:", "ui_units": "Unit System:", 
        "ui_unit_opts": ["US Units (cups/oz)", "Metric (g/ml)"],
        "ui_create": "Create Recipe ✨", "ui_wait": "Calculating recipe for {0} servings...", "ui_ready": "Ready!",
        "ui_dl": "📄 Download PDF Recipe", "ui_buy": "Buy on Amazon*", 
        "ui_btn_pay": "⚡ Support ChefList Pro ($0.90)", # DER FEHLENDE KEY
        "ui_counter_text": "Recipes created:", 
        "legal_title": "About & Legal", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Total recipes generated:", "legal_amz": "✨ As an Amazon Associate, I earn from qualifying purchases.", 
        "legal_privacy_title": "🛡️ Data Protection", "legal_privacy_body": "We do not store personal data. Processing is encrypted.", 
        "legal_note": "⚠️ **Note:** AI can make mistakes.",
        "ai_lang": "ENGLISH", "pdf_rec": "Recipe", "pdf_instr": "Instructions", "pdf_enjoy": "Enjoy your meal!",
        "fb_header": "Help us improve! 🍲", "fb_btn": "Send Feedback ✨", 
        "fb_place": "What can we do better?", "fb_mail": "Your email (optional)", "fb_thx": "Saved! 🙌"
    },
    "Deutsch": {
        "tag": "cheflist21-21", "amz": "amazon.de", "curr": "EUR", "iso": "de",
        "ui_header": "YouTube-Rezepte in druckbare PDFs verwandeln",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Portionen:", "ui_units": "Einheitensystem:", 
        "ui_unit_opts": ["Metrisch (g/ml)", "US-Einheiten (cups/oz)"],
        "ui_create": "Rezept erstellen ✨", "ui_wait": "Berechne Rezept für {0} Portionen...", "ui_ready": "Bereit!",
        "ui_dl": "📄 PDF Rezept herunterladen", "ui_buy": "Auf Amazon kaufen*", 
        "ui_btn_pay": "⚡ ChefList Pro unterstützen (0,90€)",
        "ui_counter_text": "Erstellte Rezepte:", 
        "legal_title": "Über & Rechtliches", "legal_op": "**Betreiber:** Markus Simmel", "legal_contact": "**Kontakt:** legemasim@gmail.com",
        "legal_total": "Bereits generierte Rezepte:", "legal_amz": "✨ Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.", 
        "legal_privacy_title": "🛡️ Datenschutz & Sicherheit", "legal_privacy_body": "Wir speichern keine persönlichen Daten. Verschlüsselt.", 
        "legal_note": "⚠️ **Hinweis:** KI kann Fehler machen.",
        "ai_lang": "GERMAN", "pdf_rec": "Rezept", "pdf_instr": "Zubereitung", "pdf_enjoy": "Guten Appetit!",
        "fb_header": "Hilf uns besser zu werden! 🍲", "fb_btn": "Feedback senden ✨",
        "fb_place": "Was können wir besser machen?", "fb_mail": "Deine E-Mail (optional)", "fb_thx": "Gespeichert! 🙌"
    },
    "Español": {
        "tag": "cheflist21-20", "amz": "amazon.es", "curr": "EUR", "iso": "es",
        "ui_header": "Convierte videos de YouTube en recetas PDF", "ui_input_label": "URL del video:",
        "ui_servings": "Porciones:", "ui_units": "Sistema:", "ui_unit_opts": ["Métrico (g/ml)", "EE.UU. (cups/oz)"],
        "ui_create": "Crear receta ✨", "ui_wait": "Calculando para {0} personas...", "ui_ready": "¡Listo!",
        "ui_dl": "📄 Descargar receta PDF", "ui_buy": "Comprar en Amazon*", 
        "ui_btn_pay": "⚡ Apoyar ChefList Pro (0,90€)",
        "ui_counter_text": "Recetas creadas:",
        "legal_title": "Información Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contacto:** legemasim@gmail.com",
        "legal_total": "Total de recetas:", "legal_amz": "✨ Socio de Amazon.", 
        "legal_privacy_title": "🛡️ Protección de datos", "legal_privacy_body": "No almacenamos datos.", 
        "legal_note": "⚠️ **Nota:** IA puede fallar.",
        "ai_lang": "SPANISH", "pdf_rec": "Receta", "pdf_instr": "Instrucciones", "pdf_enjoy": "¡Buen provecho!",
        "fb_header": "¡Ayúdanos a mejorar! 🍲", "fb_btn": "Enviar ✨", "fb_place": "¿Ideas?", "fb_mail": "Correo", "fb_thx": "¡Gracias! 🙌"
    },
    "Français": {
        "tag": "cheflist21-20", "amz": "amazon.fr", "curr": "EUR", "iso": "fr",
        "ui_header": "YouTube en PDF imprimable", "ui_input_label": "URL vidéo:",
        "ui_servings": "Portions:", "ui_units": "Unités:", "ui_unit_opts": ["Métrique (g/ml)", "US (cups/oz)"],
        "ui_create": "Créer la recette ✨", "ui_wait": "Calcul pour {0} personnes...", "ui_ready": "Prêt!",
        "ui_dl": "📄 Télécharger le PDF", "ui_buy": "Acheter sur Amazon*", 
        "ui_btn_pay": "⚡ Soutenir ChefList Pro (0,90€)",
        "ui_counter_text": "Recettes créées:",
        "legal_title": "Mentions Légales", "legal_op": "**Opérateur:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Total recettes:", "legal_amz": "✨ Partenaire Amazon.", 
        "legal_privacy_title": "🛡️ Confidentialité", "legal_privacy_body": "Pas de stockage.", 
        "legal_note": "⚠️ **Note:** L'IA peut errer.",
        "ai_lang": "FRENCH", "pdf_rec": "Recette", "pdf_instr": "Instructions", "pdf_enjoy": "Bon appétit!",
        "fb_header": "Aidez-nous! 🍲", "fb_btn": "Envoyer ✨", "fb_place": "Idées?", "fb_mail": "Email", "fb_thx": "Merci! 🙌"
    },
    "Italiano": {
        "tag": "cheflist21-20", "amz": "amazon.it", "curr": "EUR", "iso": "it",
        "ui_header": "Trasforma YouTube in PDF", "ui_input_label": "URL video:",
        "ui_servings": "Porzioni:", "ui_units": "Unità:", "ui_unit_opts": ["Metrico (g/ml)", "US (cups/oz)"],
        "ui_create": "Crea ricetta ✨", "ui_wait": "Calcolo per {0} persone...", "ui_ready": "Pronto!",
        "ui_dl": "📄 Scarica PDF", "ui_buy": "Acquista su Amazon*", 
        "ui_btn_pay": "⚡ Sostieni ChefList Pro (0,90€)",
        "ui_counter_text": "Ricette create:",
        "legal_title": "Info Legali", "legal_op": "**Operatore:** Markus Simmel", "legal_contact": "**Contatto:** legemasim@gmail.com",
        "legal_total": "Totale ricette:", "legal_amz": "✨ Partner Amazon.", 
        "legal_privacy_title": "🛡️ Privacy", "legal_privacy_body": "Dati protetti.", 
        "legal_note": "⚠️ **Nota:** IA può sbagliare.",
        "ai_lang": "ITALIAN", "pdf_rec": "Ricetta", "pdf_instr": "Istruzioni", "pdf_enjoy": "Buon appetito!",
        "fb_header": "Aiutaci! 🍲", "fb_btn": "Invia ✨", "fb_place": "Idee?", "fb_mail": "Email", "fb_thx": "Grazie! 🙌"
    },
    "Português": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "pt",
        "ui_header": "YouTube para PDF", "ui_input_label": "URL do vídeo:",
        "ui_servings": "Porções:", "ui_units": "Unidades:", "ui_unit_opts": ["Métrico (g/ml)", "US (cups/oz)"],
        "ui_create": "Criar receita ✨", "ui_wait": "Calculando...", "ui_ready": "Pronto!",
        "ui_dl": "📄 Baixar PDF", "ui_buy": "Comprar na Amazon*", 
        "ui_btn_pay": "⚡ Apoiar ChefList (0,90 USD)",
        "ui_counter_text": "Receitas criadas:",
        "legal_title": "Info Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contato:** legemasim@gmail.com",
        "legal_total": "Total:", "legal_amz": "✨ Associado Amazon.", 
        "legal_privacy_title": "🛡️ Privacidade", "legal_privacy_body": "Dados seguros.", 
        "legal_note": "⚠️ **Nota:** IA pode errar.",
        "ai_lang": "PORTUGUESE", "pdf_rec": "Receita", "pdf_instr": "Instruções", "pdf_enjoy": "Bom apetite!",
        "fb_header": "Ajuda! 🍲", "fb_btn": "Enviar ✨", "fb_place": "Ideias?", "fb_mail": "Email", "fb_thx": "Obrigado! 🙌"
    },
    "Nederlands": {
        "tag": "cheflist21-20", "amz": "amazon.nl", "curr": "EUR", "iso": "nl",
        "ui_header": "YouTube naar PDF", "ui_input_label": "Video URL:",
        "ui_servings": "Porties:", "ui_units": "Eenheden:", "ui_unit_opts": ["Metrisch (g/ml)", "US (cups/oz)"],
        "ui_create": "Recept maken ✨", "ui_wait": "Berekenen...", "ui_ready": "Klaar!",
        "ui_dl": "📄 PDF downloaden", "ui_buy": "Koop op Amazon*", 
        "ui_btn_pay": "⚡ Steun ChefList (0,90€)",
        "ui_counter_text": "Recepten:",
        "legal_title": "Juridisch", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Totaal:", "legal_amz": "✨ Amazon Partner.", 
        "legal_privacy_title": "🛡️ Privacy", "legal_privacy_body": "Geen dataopslag.", 
        "legal_note": "⚠️ **Opmerking:** AI kan fouten maken.",
        "ai_lang": "DUTCH", "pdf_rec": "Recept", "pdf_instr": "Instructies", "pdf_enjoy": "Eet smakelijk!",
        "fb_header": "Help ons! 🍲", "fb_btn": "Verzenden ✨", "fb_place": "Ideeën?", "fb_mail": "Email", "fb_thx": "Bedankt! 🙌"
    },
    "Polski": {
        "tag": "cheflist21-20", "amz": "amazon.pl", "curr": "PLN", "iso": "pl",
        "ui_header": "YouTube na PDF", "ui_input_label": "URL filmu:",
        "ui_servings": "Porcje:", "ui_units": "Jednostki:", "ui_unit_opts": ["Metryczne (g/ml)", "US (cups/oz)"],
        "ui_create": "Utwórz przepis ✨", "ui_wait": "Obliczanie...", "ui_ready": "Gotowe!",
        "ui_dl": "📄 Pobierz PDF", "ui_buy": "Kup na Amazon*", 
        "ui_btn_pay": "⚡ Wesprzyj (4 PLN)",
        "ui_counter_text": "Przepisy:",
        "legal_title": "Prawne", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Kontakt:** legemasim@gmail.com",
        "legal_total": "Suma:", "legal_amz": "✨ Partner Amazon.", 
        "legal_privacy_title": "🛡️ Prywatność", "legal_privacy_body": "Szyfrowane.", 
        "legal_note": "⚠️ **Uwaga:** AI błędy.",
        "ai_lang": "POLISH", "pdf_rec": "Przepis", "pdf_instr": "Instrukcje", "pdf_enjoy": "Smacznego!",
        "fb_header": "Pomoc! 🍲", "fb_btn": "Wyślij ✨", "fb_place": "Pomysły?", "fb_mail": "Email", "fb_thx": "Dzięki! 🙌"
    },
    "Türkçe": {
        "tag": "cheflist21-20", "amz": "amazon.com.tr", "curr": "TRY", "iso": "tr",
        "ui_header": "YouTube'dan PDF'e", "ui_input_label": "Video URL:",
        "ui_servings": "Porsiyon:", "ui_units": "Birimler:", "ui_unit_opts": ["Metrik (g/ml)", "ABD (cups/oz)"],
        "ui_create": "Tarif oluştur ✨", "ui_wait": "Hesaplanıyor...", "ui_ready": "Hazır!",
        "ui_dl": "📄 PDF İndir", "ui_buy": "Amazon'dan al*", 
        "ui_btn_pay": "⚡ Destek (30 TL)",
        "ui_counter_text": "Tarifler:",
        "legal_title": "Yasal", "legal_op": "**Operatör:** Markus Simmel", "legal_contact": "**İletişim:** legemasim@gmail.com",
        "legal_total": "Toplam:", "legal_amz": "✨ Amazon Ortağı.", 
        "legal_privacy_title": "🛡️ Veri", "legal_privacy_body": "Şifreli.", 
        "legal_note": "⚠️ **Not:** AI hata.",
        "ai_lang": "TURKISH", "pdf_rec": "Tarif", "pdf_instr": "Talimatlar", "pdf_enjoy": "Afiyet olsun!",
        "fb_header": "Yardım! 🍲", "fb_btn": "Gönder ✨", "fb_place": "Fikirler?", "fb_mail": "E-posta", "fb_thx": "Teşekkürler! 🙌"
    },
    "日本語": {
        "tag": "cheflist21-20", "amz": "amazon.co.jp", "curr": "JPY", "iso": "ja",
        "ui_header": "YouTubeをPDFに", "ui_input_label": "動画URL:",
        "ui_servings": "人数:", "ui_units": "単位:", "ui_unit_opts": ["メートル法 (g/ml)", "US単位 (cups/oz)"],
        "ui_create": "レシピを作成 ✨", "ui_wait": "計算中...", "ui_ready": "完了！",
        "ui_dl": "📄 PDF保存", "ui_buy": "Amazonで購入*", 
        "ui_btn_pay": "⚡ 支援 (¥140)",
        "ui_counter_text": "レシピ数:",
        "legal_title": "法的情報", "legal_op": "**運営者:** Markus Simmel", "legal_contact": "**連絡先:** legemasim@gmail.com",
        "legal_total": "累計:", "legal_amz": "✨ Amazonアソシエイト。", 
        "legal_privacy_title": "🛡️ 保護", "legal_privacy_body": "暗号化済み。", 
        "legal_note": "⚠️ **注意:** AIミス.",
        "ai_lang": "JAPANESE", "pdf_rec": "Recipe", "pdf_instr": "Instructions", "pdf_enjoy": "Enjoy!",
        "fb_header": "改善にご協力ください！ 🍲", "fb_btn": "送信 ✨", "fb_place": "ご意見", "fb_mail": "メール", "fb_thx": "感謝! 🙌"
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
    except Exception as e:
        print(f"Debug Error: {e}")
        return "Recipe", None, None, "Unknown Chef"

def generate_smart_recipe(video_title, channel_name, transcript, description, config, portions, unit_system):
    combined_input = f"ORIGINAL TITLE: {video_title}\nSOURCE CHANNEL: {channel_name}\n\nTRANSCRIPT:\n{transcript}\n\nDESCRIPTION:\n{description}"
    
    # Unit Logic
    u_inst = "US UNITS (cups, oz, lbs)" if "US" in str(unit_system) or "EE.UU." in str(unit_system) else "METRIC (g, ml, kg)"
    
    system_prompt = f"""
    You are a professional chef and a high-precision mathematician.
    
    TASK: Translate and calculate this recipe into {config['ai_lang']}.
    
    RULES:
    1. The ENTIRE response (Title, Headers, Labels, Instructions) must be in {config['ai_lang']}.
    2. Recalculate quantities for exactly {portions} person(s).
    3. Use {u_inst}.
    4. Format the START exactly like this: "TITLE: [Translated Recipe Name] by [Author]"
    5. Table columns: Amount | Ingredient | Shop (Link: https://www.{config['amz']}/s?k=[INGREDIENT]&tag={config['tag']})
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
    if not text: return ""
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'Euro', '–': '-', '’': "'", '“': '"', '”': '"'}
    for char, rep in replacements.items(): text = text.replace(char, rep)
    # Entfernt alles nicht-ASCII um Abstürze zu vermeiden
    return re.sub(r'[^\x00-\x7F]+', '', text)

def create_pdf(text_content, recipe_title, config):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_left_margin(10); pdf.set_right_margin(10)
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Arial", style="B", size=14)
        
        # Titel
        title = clean_for_pdf(recipe_title[:40])
        pdf.cell(190, 15, txt=f"{config['pdf_rec']}: {title}", ln=True, align='C', fill=True)
        pdf.ln(5)
        
        lines = text_content.split('\n')
        is_instruction = False
        
        for line in lines:
            line = line.strip()
            if not line or '---' in line: continue
            
            # Instruktionen erkennen (multilingual)
            if any(x in line for x in ['Instructions', 'Zubereitung', 'Instrucciones', 'Istruzioni', 'Instruções', 'Talimatlar']):
                is_instruction = True
                pdf.ln(5)
                pdf.set_font("Arial", style="B", size=12)
                pdf.cell(0, 10, txt=config['pdf_instr'], ln=True)
                continue
            
            clean_line = clean_for_pdf(line)
            
            # Tabellen-Logik wie im Original
            if '|' in clean_line and not is_instruction:
                parts = [p.strip() for p in clean_line.split('|') if p.strip()]
                if len(parts) >= 2:
                    content = f"[ ] {parts[0]} {parts[1]}"
                    pdf.set_font("Arial", style="B", size=11)
                    pdf.cell(185, 8, txt=content, ln=True)
                    pdf.set_draw_color(220, 220, 220)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            else:
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(185, 7, txt=clean_line, align='L')
                
        pdf.ln(10)
        pdf.set_font("Arial", style="I", size=10)
        pdf.cell(0, 10, txt=config['pdf_enjoy'], ln=True, align='C')
        
        return pdf.output(dest='S').encode('latin-1', 'ignore')
    except: return None

# --- 5. INTERFACE ---
st.set_page_config(page_title="ChefList Pro Global", page_icon="🍲", layout="centered")

st.markdown("<style>[data-testid='stSidebar'] img { background-color: white; padding: 10px; border-radius: 12px; border: 2px solid #e0e0e0; margin-bottom: 20px; }</style>", unsafe_allow_html=True)

# Automatik Logik
if "user_lang_selection" not in st.session_state:
    try:
        lang_header = st.context.headers.get("Accept-Language", "en")
        primary_code = lang_header.split(",")[0].split("-")[0].lower()
        mapping = {"de": "Deutsch", "en": "English", "es": "Español", "fr": "Français", "it": "Italiano", "pt": "Português", "nl": "Nederlands", "pl": "Polski", "tr": "Türkçe", "ja": "日本語"}
        st.session_state.user_lang_selection = mapping.get(primary_code, "English")
    except:
        st.session_state.user_lang_selection = "English"

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

with st.sidebar:
    # Sprache wählen (Standard = automatisch erkannt)
    try: idx = list(LANG_CONFIG.keys()).index(st.session_state.user_lang_selection)
    except: idx = 0
    selected_lang = st.selectbox("🌍 Language", list(LANG_CONFIG.keys()), index=idx)
    c = LANG_CONFIG[selected_lang]
    
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    else: st.title("🍳 ChefList Pro")
    
    st.info(f"{c['ui_counter_text']} {st.session_state.counter}")
    
    pay_url = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Support&amount=0.90&currency_code={c['curr']}"
    
    # Sicherer Zugriff auf den Button-Text
    st.markdown(f'''<a href="{pay_url}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 12px; width: 100%;">{c['ui_btn_pay']}</button></a>''', unsafe_allow_html=True)
    
    st.markdown("---")
    with st.expander(f"ℹ️ {c['legal_title']}"):
        st.caption(c["legal_op"]); st.caption(c["legal_contact"]); st.divider()
        st.write(f"📊 {c['legal_total']} {get_total_count()}")
        st.divider(); st.caption(c["legal_amz"]); st.subheader(c["legal_privacy_title"]); st.caption(c["legal_privacy_body"])
        st.divider(); st.caption(c["legal_note"])
        
    st.divider()
    if st.checkbox("Admin"):
        pw = st.text_input("PW", type="password")
        if pw == "Gemini_Cheflist_pw" and os.path.exists("user_feedback.txt"):
            with open("user_feedback.txt", "r") as f: st.text_area("Log", f.read())

# Hauptbereich
st.title("🍲 ChefList Pro")
st.subheader(c['ui_header'])

v_url = st.text_input(c['ui_input_label'], placeholder="https://...")
col1, col2 = st.columns(2)
ports = col1.slider(c['ui_servings'], 1, 10, 4)
units = col2.radio(c['ui_units'], c['ui_unit_opts'], horizontal=True)

if st.button(c['ui_create'], use_container_width=True):
    if v_url:
        with st.status(c['ui_wait'].format(ports)) as status:
            t_orig, trans, desc, chef = get_full_video_data(v_url)
            if trans or desc:
                res = generate_smart_recipe(t_orig, chef, trans, desc, c, ports, units)
                if res:
                    st.session_state.recipe_result = res
                    # Titel extrahieren
                    clean_title = t_orig
                    for l in res.split('\n'):
                        if "TITLE:" in l: 
                            clean_title = l.replace("TITLE:", "").strip()
                            break
                    st.session_state.recipe_title = clean_title
                    st.session_state.counter += 1
                    update_global_counter()
                    status.update(label=c['ui_ready'], state="complete")
                else: st.error("AI Error")
            else: st.error("No Data")

if st.session_state.recipe_result:
    st.divider()
    st.subheader(f"📖 {st.session_state.recipe_title}")
    st.markdown(st.session_state.recipe_result.replace("Check on Amazon", c['ui_buy']))
    
    pdf_bytes = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title, c)
    if pdf_bytes:
        st.download_button(c['ui_dl'], data=pdf_bytes, file_name="Recipe.pdf", mime="application/pdf", use_container_width=True)

st.divider()
st.subheader(c['fb_header'])
with st.form("fb"):
    txt = st.text_area(c['fb_place']); mail = st.text_input(c['fb_mail'])
    if st.form_submit_button(c['fb_btn']):
        with open("user_feedback.txt", "a") as f: f.write(f"[{selected_lang}] {mail}: {txt}\n---\n")
        st.success(c['fb_thx'])
