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
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "en",
        "ui_header": "Convert YouTube recipes into printable PDFs",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Servings:", "ui_units": "Units:", 
        "ui_unit_opts": ["US Units (cups/oz)", "Metric (g/ml)"],
        "ui_create": "Create Recipe ✨", "ui_wait": "Calculating for {0} servings...", "ui_ready": "Ready!",
        "ui_dl": "📄 Download PDF Recipe", "ui_buy": "Buy on Amazon*", "ui_table_header": "Shop Ingredients",
        "ui_btn_pay": "⚡ Support ChefList Pro ($0.90)",
        "ui_counter_text": "Recipes created:", 
        "legal_title": "About & Legal", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Total recipes:", 
        "legal_amz": "✨ As an Amazon Associate, I earn from qualifying purchases.", 
        "legal_privacy_title": "🛡️ Data Protection", 
        "legal_privacy_body": "We do not store personal data. Processing is encrypted.", 
        "legal_note": "⚠️ **Note:** This app uses AI. AI can make mistakes – please check details (e.g., baking times) before cooking.",
        "ai_lang": "ENGLISH", 
        "fb_header": "Help us improve! 🍲", "fb_btn": "Send ✨", 
        "fb_place": "What can we do better?", "fb_mail": "Email (optional)", "fb_thx": "Saved! 🙌",
        "pdf_rec": "Recipe", "pdf_instr": "Instructions", 
        "pdf_enjoy": "Happy cooking from the Cheflist Pro Team!"
    },
    "Deutsch": {
        "tag": "cheflist21-21", "amz": "amazon.de", "curr": "EUR", "iso": "de",
        "ui_header": "YouTube-Rezepte in druckbare PDFs verwandeln",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Portionen:", "ui_units": "Einheiten:", 
        "ui_unit_opts": ["Metrisch (g/ml)", "US-Einheiten (cups/oz)"],
        "ui_create": "Rezept erstellen ✨", "ui_wait": "Berechne für {0} Portionen...", "ui_ready": "Bereit!",
        "ui_dl": "📄 PDF herunterladen", "ui_buy": "Auf Amazon kaufen*", "ui_table_header": "Zutaten einkaufen",
        "ui_btn_pay": "⚡ ChefList Pro unterstützen (0,90€)",
        "ui_counter_text": "Erstellte Rezepte:", 
        "legal_title": "Über & Rechtliches", "legal_op": "**Betreiber:** Markus Simmel", "legal_contact": "**Kontakt:** legemasim@gmail.com",
        "legal_total": "Gesamt Rezepte:", 
        "legal_amz": "✨ Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.", 
        "legal_privacy_title": "🛡️ Datenschutz", 
        "legal_privacy_body": "Wir speichern keine persönlichen Daten. Die Verarbeitung erfolgt verschlüsselt.", 
        "legal_note": "⚠️ **Hinweis:** Diese App nutzt eine KI. KI kann Fehler machen – bitte prüfe die Angaben (z.B. Backzeiten) vor dem Kochen.",
        "ai_lang": "GERMAN", 
        "fb_header": "Hilf uns besser zu werden! 🍲", "fb_btn": "Senden ✨",
        "fb_place": "Was können wir besser machen?", "fb_mail": "E-Mail (optional)", "fb_thx": "Gespeichert! 🙌",
        "pdf_rec": "Rezept", "pdf_instr": "Zubereitung", 
        "pdf_enjoy": "Gutes Gelingen wünscht das Team von Cheflist Pro."
    },
    "Español": {
        "tag": "cheflist21-20", "amz": "amazon.es", "curr": "EUR", "iso": "es",
        "ui_header": "YouTube a PDF", "ui_input_label": "URL del video:",
        "ui_servings": "Porciones:", "ui_units": "Unidades:", "ui_unit_opts": ["Métrico (g/ml)", "EE.UU. (cups/oz)"],
        "ui_create": "Crear ✨", "ui_wait": "Calculando...", "ui_ready": "¡Listo!",
        "ui_dl": "📄 Descargar PDF", "ui_buy": "Comprar en Amazon*", "ui_table_header": "Comprar ingredientes",
        "ui_btn_pay": "⚡ Apoyar ChefList Pro (0,90€)",
        "ui_counter_text": "Recetas:", 
        "legal_title": "Info Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contacto:** legemasim@gmail.com",
        "legal_total": "Total recetas:", 
        "legal_amz": "✨ Como asociado de Amazon, gano por las compras calificadas.", 
        "legal_privacy_title": "🛡️ Privacidad", 
        "legal_privacy_body": "No almacenamos datos personales. El procesamiento está cifrado.", 
        "legal_note": "⚠️ **Nota:** Esta aplicación utiliza IA. La IA puede cometer errores; por favor, verifique los detalles (p. ej., tiempos de cocción) antes de cocinar.",
        "ai_lang": "SPANISH", "fb_header": "¡Ayúdanos! 🍲", "fb_btn": "Enviar ✨",
        "fb_place": "¿Ideas?", "fb_mail": "Correo", "fb_thx": "¡Gracias! 🙌",
        "pdf_rec": "Receta", "pdf_instr": "Instrucciones", 
        "pdf_enjoy": "¡El equipo de Cheflist Pro le desea mucho éxito!"
    },
    "Français": {
        "tag": "cheflist21-20", "amz": "amazon.fr", "curr": "EUR", "iso": "fr",
        "ui_header": "YouTube en PDF", "ui_input_label": "URL vidéo:",
        "ui_servings": "Portions:", "ui_units": "Unités:", "ui_unit_opts": ["Métrique (g/ml)", "US (cups/oz)"],
        "ui_create": "Créer ✨", "ui_wait": "Calcul...", "ui_ready": "Prêt!",
        "ui_dl": "📄 Télécharger le PDF", "ui_buy": "Acheter sur Amazon*", "ui_table_header": "Acheter les ingrédients",
        "ui_btn_pay": "⚡ Soutenir ChefList Pro (0,90€)",
        "ui_counter_text": "Recettes:", 
        "legal_title": "Mentions Légales", "legal_op": "**Opérateur:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Total recettes:", 
        "legal_amz": "✨ En tant que partenaire Amazon, je réalise un bénéfice sur les achats remplissant les conditions requises.", 
        "legal_privacy_title": "🛡️ Confidentialité", 
        "legal_privacy_body": "Nous ne stockons pas de données personnelles. Le traitement est crypté.", 
        "legal_note": "⚠️ **Remarque:** Cette application utilise l'IA. L'IA peut faire des erreurs - veuillez vérifier les détails (ex: temps de cuisson) avant de cuisiner.",
        "ai_lang": "FRENCH", "fb_header": "Aidez-nous! 🍲", "fb_btn": "Envoyer ✨",
        "fb_place": "Idées?", "fb_mail": "Email", "fb_thx": "Merci! 🙌",
        "pdf_rec": "Recette", "pdf_instr": "Instructions", 
        "pdf_enjoy": "L'équipe de Cheflist Pro vous souhaite une bonne réussite !"
    },
    "Italiano": {
        "tag": "cheflist21-20", "amz": "amazon.it", "curr": "EUR", "iso": "it",
        "ui_header": "YouTube in PDF", "ui_input_label": "URL video:",
        "ui_servings": "Porzioni:", "ui_units": "Unità:", "ui_unit_opts": ["Metrico (g/ml)", "US (cups/oz)"],
        "ui_create": "Crea ✨", "ui_wait": "Calcolo...", "ui_ready": "Pronto!",
        "ui_dl": "📄 Scarica PDF", "ui_buy": "Acquista su Amazon*", "ui_table_header": "Acquista ingredienti",
        "ui_btn_pay": "⚡ Sostieni ChefList Pro (0,90€)",
        "ui_counter_text": "Ricette:", 
        "legal_title": "Info Legali", "legal_op": "**Operatore:** Markus Simmel", "legal_contact": "**Contatto:** legemasim@gmail.com",
        "legal_total": "Totale ricette:", 
        "legal_amz": "✨ In qualità di Affiliato Amazon, ricevo un guadagno dagli acquisti idonei.", 
        "legal_privacy_title": "🛡️ Privacy", 
        "legal_privacy_body": "Non memorizziamo dati personali. L'elaborazione è crittografata.", 
        "legal_note": "⚠️ **Nota:** Questa app utilizza l'IA. L'IA può commettere errori: controlla i dettagli (es. tempi di cottura) prima di cucinare.",
        "ai_lang": "ITALIAN", "fb_header": "Aiutaci! 🍲", "fb_btn": "Invia ✨",
        "fb_place": "Idee?", "fb_mail": "Email", "fb_thx": "Grazie! 🙌",
        "pdf_rec": "Ricetta", "pdf_instr": "Istruzioni", 
        "pdf_enjoy": "Buona fortuna dal team di Cheflist Pro!"
    },
    "Português": {
        "tag": "cheflist21-20", "amz": "amazon.com.br", "curr": "BRL", "iso": "pt",
        "ui_header": "YouTube para PDF", "ui_input_label": "URL do vídeo:",
        "ui_servings": "Porções:", "ui_units": "Unidades:", "ui_unit_opts": ["Métrico (g/ml)", "US (cups/oz)"],
        "ui_create": "Criar ✨", "ui_wait": "Calculando...", "ui_ready": "Pronto!",
        "ui_dl": "📄 Baixar PDF", "ui_buy": "Comprar na Amazon*", "ui_table_header": "Comprar ingredientes",
        "ui_btn_pay": "⚡ Apoiar ChefList Pro (0,90€)",
        "ui_counter_text": "Receitas:", 
        "legal_title": "Info Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contacto:** legemasim@gmail.com",
        "legal_total": "Total:", 
        "legal_amz": "✨ Como associado da Amazon, ganho com compras qualificadas.", 
        "legal_privacy_title": "🛡️ Privacidade", 
        "legal_privacy_body": "Não armazenamos dados pessoais. O processamento é criptografado.", 
        "legal_note": "⚠️ **Nota:** Este aplicativo usa IA. A IA pode cometer erros – verifique os detalhes (ex: tempos de cozimento) antes de cozinhar.",
        "ai_lang": "PORTUGUESE", "fb_header": "Ajuda! 🍲", "fb_btn": "Enviar ✨",
        "fb_place": "Ideias?", "fb_mail": "Email", "fb_thx": "Obrigado! 🙌",
        "pdf_rec": "Receita", "pdf_instr": "Instruções", 
        "pdf_enjoy": "Boa sorte da equipa Cheflist Pro!"
    },
    "Nederlands": {
        "tag": "cheflist21-20", "amz": "amazon.nl", "curr": "EUR", "iso": "nl",
        "ui_header": "YouTube naar PDF", "ui_input_label": "Video URL:",
        "ui_servings": "Porties:", "ui_units": "Eenheden:", "ui_unit_opts": ["Metrisch (g/ml)", "US (cups/oz)"],
        "ui_create": "Maken ✨", "ui_wait": "Berekenen...", "ui_ready": "Klaar!",
        "ui_dl": "📄 PDF downloaden", "ui_buy": "Koop op Amazon*", "ui_table_header": "Ingrediënten kopen",
        "ui_btn_pay": "⚡ ChefList Pro steunen (0,90€)",
        "ui_counter_text": "Recepten:",
        "legal_title": "Juridisch", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Totaal:", 
        "legal_amz": "✨ Als Amazon-partner verdien ik aan gekwalificeerde aankopen.", 
        "legal_privacy_title": "🛡️ Privacy", 
        "legal_privacy_body": "Wij slaan geen persoonlijke gegevens op. Verwerking is versleuteld.", 
        "legal_note": "⚠️ **Let op:** Deze app maakt gebruik van AI. AI kan fouten maken - controleer de details (bijv. baktijden) voordat u gaat koken.",
        "ai_lang": "DUTCH", "fb_header": "Help ons! 🍲", "fb_btn": "Verzenden ✨",
        "fb_place": "Ideeën?", "fb_mail": "Email", "fb_thx": "Bedankt! 🙌",
        "pdf_rec": "Recept", "pdf_instr": "Instructies", 
        "pdf_enjoy": "Veel succes gewenst door het Cheflist Pro team."
    },
    "Polski": {
        "tag": "cheflist21-20", "amz": "amazon.pl", "curr": "PLN", "iso": "pl",
        "ui_header": "YouTube na PDF", "ui_input_label": "URL filmu:",
        "ui_servings": "Porcje:", "ui_units": "Jednostki:", "ui_unit_opts": ["Metryczne (g/ml)", "US (cups/oz)"],
        "ui_create": "Utwórz ✨", "ui_wait": "Obliczanie...", "ui_ready": "Gotowe!",
        "ui_dl": "📄 Pobierz PDF", "ui_buy": "Kup na Amazon*", "ui_table_header": "Kup składniki",
        "ui_btn_pay": "⚡ Wesprzyj ChefList Pro (4 PLN)",
        "ui_counter_text": "Przepisy:", 
        "legal_title": "Prawne", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Kontakt:** legemasim@gmail.com",
        "legal_total": "Suma:", 
        "legal_amz": "✨ Jako partner Amazon zarabiam na kwalifikujących się zakupach.", 
        "legal_privacy_title": "🛡️ Prywatność", 
        "legal_privacy_body": "Nie przechowujemy danych osobowych. Przetwarzanie jest szyfrowane.", 
        "legal_note": "⚠️ **Uwaga:** Ta aplikacja korzysta z AI. AI może popełniać błędy – sprawdź szczegóły (np. czas pieczenia) przed gotowaniem.",
        "ai_lang": "POLISH", "fb_header": "Pomoc! 🍲", "fb_btn": "Wyślij ✨",
        "fb_place": "Pomysły?", "fb_mail": "Email", "fb_thx": "Dzięki! 🙌",
        "pdf_rec": "Przepis", "pdf_instr": "Instrukcje", 
        "pdf_enjoy": "Powodzenia życzy zespół Cheflist Pro."
    },
    "Türkçe": {
        "tag": "cheflist21-20", "amz": "amazon.com.tr", "curr": "TRY", "iso": "tr",
        "ui_header": "YouTube'dan PDF'e", "ui_input_label": "Video URL:",
        "ui_servings": "Porsiyon:", "ui_units": "Birimler:", "ui_unit_opts": ["Metrik (g/ml)", "ABD (cups/oz)"],
        "ui_create": "Oluştur ✨", "ui_wait": "Hesaplanıyor...", "ui_ready": "Hazır!",
        "ui_dl": "📄 PDF İndir", "ui_buy": "Amazon'dan al*", "ui_table_header": "Malzemeleri satın al",
        "ui_btn_pay": "⚡ ChefList Pro'yu Destekle (30 TL)",
        "ui_counter_text": "Tarifler:", 
        "legal_title": "Yasal", "legal_op": "**Operatör:** Markus Simmel", "legal_contact": "**İletişim:** legemasim@gmail.com",
        "legal_total": "Toplam:", 
        "legal_amz": "✨ Bir Amazon ortağı olarak kalifiye satışlardan kazanç sağlıyorum.", 
        "legal_privacy_title": "🛡️ Veri", 
        "legal_privacy_body": "Kişisel verileri saklamıyoruz. İşleme şifrelidir.", 
        "legal_note": "⚠️ **Not:** Bu uygulama bir yapay zeka (AI) kullanır. AI hata yapabilir - lütfen pişirmeden önce ayrıntıları (örneğin pişirme sürelerini) kontrol edin.",
        "ai_lang": "TURKISH", "fb_header": "Yardım! 🍲", "fb_btn": "Gönder ✨",
        "fb_place": "Fikirler?", "fb_mail": "E-posta", "fb_thx": "Teşekkürler! 🙌",
        "pdf_rec": "Tarif", "pdf_instr": "Talimatlar", 
        "pdf_enjoy": "Cheflist Pro ekibi başarılar diler."
    },
    "日本語": {
        "tag": "cheflist21-20", "amz": "amazon.co.jp", "curr": "JPY", "iso": "ja",
        "ui_header": "YouTubeをPDFに", "ui_input_label": "動画URL:",
        "ui_servings": "人数:", "ui_units": "単位:", "ui_unit_opts": ["メートル法 (g/ml)", "US単位 (cups/oz)"],
        "ui_create": "作成 ✨", "ui_wait": "計算中...", "ui_ready": "完了！",
        "ui_dl": "📄 PDF保存", "ui_buy": "Amazonで購入*", "ui_table_header": "材料を購入する",
        "ui_btn_pay": "⚡ ChefList Proを支援 (¥140)",
        "ui_counter_text": "レシピ数:", 
        "legal_title": "法的情報", "legal_op": "**運営者:** Markus Simmel", "legal_contact": "**連絡先:** legemasim@gmail.com",
        "legal_total": "累計:", 
        "legal_amz": "✨ Amazonアソシエイトとして、適格販売により収入を得ています。", 
        "legal_privacy_title": "🛡️ 保護", 
        "legal_privacy_body": "個人データは保存されません。処理は暗号化されています。", 
        "legal_note": "⚠️ **注意:** このアプリはAIを使用しています。AIは間違いを犯す可能性があります。調理前に詳細（焼き時間など）を確認してください。",
        "ai_lang": "JAPANESE", "fb_header": "改善にご協力ください！ 🍲", "fb_btn": "送信 ✨",
        "fb_place": "ご意見", "fb_mail": "メール", "fb_thx": "感謝! 🙌",
        "pdf_rec": "Recipe", "pdf_instr": "Instructions", 
        "pdf_enjoy": "Cheflist Proチームより、幸運を祈ります！"
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
    u_inst = "US UNITS (cups, oz)" if "US" in str(unit_system) or "EE.UU." in str(unit_system) else "METRIC (g, ml)"
    
    buy_text = config['ui_buy'].replace('*', '')
    table_header = config.get('ui_table_header', 'Shop Ingredients')
    instr_header = config.get('pdf_instr', 'Instructions')
    
    # Sprach-Mapping für Tabellenköpfe
    lang_map = {
        "de": ("Menge", "Zutat"), "en": ("Amount", "Ingredient"), "es": ("Cantidad", "Ingrediente"),
        "fr": ("Quantite", "Ingredient"), "it": ("Quantita", "Ingrediente"), "pl": ("Ilosc", "Skladnik"),
        "tr": ("Miktar", "Malzeme"), "nl": ("Hoeveelheid", "Ingredient")
    }
    h_amount, h_ingredient = lang_map.get(config['iso'], ("Amount", "Ingredient"))
    base_url = f"https://www.{config['amz']}/s?k="
    tag_part = f"&tag={config['tag']}"

    # VERBESSERTER SYSTEM PROMPT MIT FOKUS AUF MATHEMATIK
    system_prompt = f"""
    You are a professional chef and a precise mathematician. Respond in {config['ai_lang']}.
    
    TARGET SERVINGS: {portions}
    TARGET UNITS: {u_inst}

    ### CORE TASK:
    1. ANALYZE: Identify the original serving size from the transcript (usually 1, 2, or 4). If not mentioned, assume 4 servings.
    2. CALCULATE: Divide original amounts by original servings, then multiply by {portions}. 
    3. VERIFY: The amounts in your table MUST be different if {portions} is not the original serving size. 
    
    ### STRUCTURE:
    | {h_amount} | {h_ingredient} | {table_header} |
    |---|---|---|
    [Ingredients with recalculated amounts]

    ### {instr_header}
    1. [Extremely detailed step 1]
    2. [Extremely detailed step 2]
    ...
    
    # CRITICAL INSTRUCTIONS:
    1. THE COOKING STEPS MUST BE LONG AND DETAILED. Do not summarize. Explain exactly how to prepare, cook, and serve the dish based on the transcript.
    2. Write at least 4-8 comprehensive steps if the transcript allows it.
    3. The third column MUST use this link format: [{buy_text}]({base_url}[KEYWORD]{tag_part})
    4. Replace [KEYWORD] with the simple English noun of the ingredient.
    5. NO title, NO author. Start directly with the table.
    6. Numbering (1., 2., ...) ONLY in the {instr_header} section.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_prompt}, 
                {"role": "user", "content": f"VIDEO: {video_title}\nTRANSCRIPT: {transcript[:12000]}\nDESCRIPTION: {description[:2000]}"}
            ],
            temperature=0.1 # Niedrige Temperatur für präzisere Rechnungen
        )
        return response.choices[0].message.content
    except: return None
    
# --- 4. PDF GENERATOR (FIXED ALIGNMENT & SPACING) ---
def clean_for_pdf(text):
    if not text: return ""
    text = str(text)
    
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 
        'ß': 'ss',
        'é': 'e', 'è': 'e', 'à': 'a', 'ù': 'u', 'ç': 'c', 
        'ñ': 'n', 'í': 'i', 'ó': 'o', 'ú': 'u',
        '€': 'EUR', '„': '"', '“': '"', '”': '"', '’': "'", '–': '-'
    }
    
    for char, rep in replacements.items():
        text = text.replace(char, rep)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text

def create_pdf(text_content, recipe_title, config):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_left_margin(15); pdf.set_right_margin(10)
        pdf.add_page()
        pdf.set_fill_color(230, 230, 230)
        
        # Logo
        if os.path.exists("logo.png"):
            try: pdf.image("logo.png", x=165, y=10, w=25)
            except: pass

        # Titel
        pdf.set_font("Arial", style="B", size=14)
        safe_rec = clean_for_pdf(config.get('pdf_rec', 'Recipe'))
        safe_title = clean_for_pdf(recipe_title if len(recipe_title) <= 40 else recipe_title[:37] + "...")
        pdf.cell(150, 15, txt=f"{safe_title}", ln=True, align='L', fill=True)
        pdf.ln(5)
        
        lines = text_content.split('\n')
        is_instruction = False
        
        for line in lines:
            line = line.strip()
            if not line or '---' in line: continue
            
            clean_line = clean_for_pdf(line)
            if not clean_line: continue
            
            # Reset X-Position am Anfang jeder Zeile, um Verschiebung zu verhindern
            pdf.set_x(15)
            
            # 1. Überschriften (Instructions, Zubereitung...)
            safe_instr_key = clean_for_pdf(config.get('pdf_instr', 'Instructions'))
            check_words = ['Instructions', 'Preparation', 'Directions', 'Zubereitung', 'Instrucciones', 'Istruzioni', safe_instr_key]
            
            if any(word.lower() in clean_line.lower() for word in check_words) and len(clean_line) < 50:
                is_instruction = True
                pdf.ln(4)
                pdf.set_font("Arial", style="B", size=12)
                pdf.cell(0, 10, txt=clean_line, ln=True)
                pdf.ln(2)
                continue

            # 2. Metadaten (Zeit, Portionen...)
            headers = ['Time', 'Difficulty', 'Temp', 'Servings', 'Units', 'Zeit', 'Dauer']
            if any(clean_line.startswith(h) for h in headers):
                pdf.set_font("Arial", style="B", size=11)
                pdf.cell(0, 8, txt=clean_line, ln=True)
                continue
                
            # 3. Tabelle (Zutaten)
            if '|' in line and not is_instruction:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    if any(x in parts[0] for x in ["Amount", "Menge", "Ingredient", "Zutat"]):
                        pdf.set_font("Arial", style="B", size=10)
                        content = f"{parts[0].upper()} - {parts[1].upper()}"
                    else:
                        pdf.set_font("Arial", style="B", size=11)
                        # Wir entfernen Klammern und Sterne, aber fügen KEINEN Bindestrich hinzu
                        clean_amount = parts[0].replace('*','').replace('[','').replace(']','').strip()
                        clean_ingredient = parts[1].replace('*','').replace('[','').replace(']','').strip()
                        # Direkte Ausgabe: "500g Mehl"
                        content = f"{clean_amount} {clean_ingredient}"
                    
                    pdf.cell(175, 8, txt=content, ln=True)
                    pdf.set_draw_color(220, 220, 220)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            
            # 4. Kochtext / Instruktionen (Der Teil der verschoben war)
            else:
                pdf.set_font("Arial", size=10)
                # multi_cell braucht eine feste Breite. 0 bedeutet bis zum rechten Rand.
                # Wir setzen die X-Position vor multi_cell explizit.
                pdf.set_x(15)
                pdf.multi_cell(180, 6, txt=clean_line.replace('*', ''), align='L')
                # Kleiner Abstand nach jedem Absatz/Schritt
                pdf.ln(2)
                
        # Footer am Ende
        pdf.ln(10)
        pdf.set_font("Arial", style="I", size=10)
        pdf.set_x(10)
        safe_enjoy = clean_for_pdf(config.get('pdf_enjoy', 'Enjoy!'))
        pdf.cell(0, 10, txt=safe_enjoy, ln=True, align='C')
        
        return pdf.output()
    except Exception as e:
        print(f"PDF Debug: {e}")
        return None        
        
# --- 5. INTERFACE ---
st.set_page_config(page_title="ChefList Pro Global", page_icon="🍲")
st.markdown("""
<style>
    /* Hauptüberschrift zentrieren */
    h1 { text-align: center; color: #FF4B4B; }
    h3 { text-align: center; color: #555; }

    /* 1. Der "Rezept erstellen" Button (Standard) -> BLAU */
    div.stButton > button {
        width: 100%;
        background-color: #0070ba; /* Royal Blue (seriös) */
        color: white;
        font-weight: bold;
        border: none;
        padding: 15px;
        font-size: 18px;
        border-radius: 8px;
    }
    div.stButton > button:hover {
        background-color: #005a9e; /* Dunkleres Blau beim Drüberfahren */
        color: white;
        border: none;
    }

    /* 2. Der "PDF Download" Button -> ROT */
    /* Wir nutzen den spezifischen Selektor für Download-Buttons */
    [data-testid="stDownloadButton"] > button {
        width: 100%;
        background-color: #FF4B4B !important; /* Signalrot */
        color: white !important;
        font-weight: bold;
        border: none;
        padding: 15px;
        font-size: 18px;
        border-radius: 8px;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background-color: #cc0000 !important; /* Dunkleres Rot beim Drüberfahren */
        color: white !important;
    }

    /* Sidebar Bild schön einrahmen */
    [data-testid='stSidebar'] img {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    /* Erzwingt volle Breite für Tabellen */
   .stMarkdown table {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)
if "user_lang_selection" not in st.session_state:
    try:
        lang_header = st.context.headers.get("Accept-Language", "en")
        primary = lang_header.split(",")[0].split("-")[0].lower()
        m = {"de": "Deutsch", "en": "English", "es": "Español", "fr": "Français", "it": "Italiano", "pt": "Português", "nl": "Nederlands", "pl": "Polski", "tr": "Türkçe", "ja": "日本語"}
        st.session_state.user_lang_selection = m.get(primary, "English")
    except: st.session_state.user_lang_selection = "English"

if "last_params" not in st.session_state: st.session_state.last_params = {}
if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

with st.sidebar:
    # 1. Sprachauswahl
    current_lang = st.session_state.get("user_lang_selection", "English")
    with st.expander(f"🌍 Language: {current_lang}", expanded=False):
        lang_options = list(LANG_CONFIG.keys())
        try: curr_index = lang_options.index(current_lang)
        except: curr_index = 0
            
        selected_lang = st.radio(
            "Sprache wählen",
            options=lang_options,
            index=curr_index,
            label_visibility="collapsed",
            key="lang_radio"
        )
        if selected_lang != current_lang:
            st.session_state.user_lang_selection = selected_lang
            st.rerun()

    c = LANG_CONFIG[selected_lang]
    
    # 2. Logo & Support
    if os.path.exists("logo.png"): 
        st.image("logo.png", use_container_width=True)
    else: 
        st.markdown(f"### 🍳 ChefList Pro")
     
    pay_url = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Support&amount=0.90&currency_code={c['curr']}"
    st.markdown(f'''<a href="{pay_url}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 14px; width:100%;">{c['ui_btn_pay']}</button></a>''', unsafe_allow_html=True)

    # 3. Rechtliches & Admin
    st.markdown("---")
    with st.expander(f"ℹ️ {c['legal_title']}"):
        st.caption(c["legal_op"])
        st.caption(c["legal_contact"])
        st.divider()
        st.write(f"📊 {c['legal_total']} {get_total_count()}")
        st.divider()
        st.caption(c["legal_amz"])
        st.subheader(c["legal_privacy_title"])
        st.caption(c["legal_privacy_body"])
        st.divider()
        st.caption(c["legal_note"])
        
        st.divider()
        if st.checkbox("Admin Mode"):
            pw = st.text_input("Password", type="password")
            if pw == "Gemini_Cheflist_pw" and os.path.exists("user_feedback.txt"):
                with open("user_feedback.txt", "r") as f: 
                    st.text_area("Feedback Log", f.read(), height=200)

# --- AB HIER: HAUPTFENSTER (Nicht mehr eingerückt!) ---

st.title("🍲 ChefList Pro")
st.subheader(c['ui_header'])

v_url = st.text_input(c['ui_input_label'], placeholder="https://...")

# --- OPTISCH SCHÖNE EINGABE ---
col_p, col_u, col_spacer = st.columns([0.5, 1, 1])

with col_p:
    # Number Input begrenzt auf 99 (2 Stellen)
    ports = st.number_input(
        f"👥 {c['ui_servings']}", 
        min_value=1, 
        max_value=99, 
        value=4, 
        step=1
    )

with col_u:
    # Radio Buttons für Einheiten
    units = st.radio(
        f"⚖️ {c['ui_units']}", 
        c['ui_unit_opts'], 
        horizontal=True
    )

# 1. ZUERST: Parameter definieren
current_params = {"url": v_url, "ports": ports, "units": units}
params_changed = current_params != st.session_state.last_params and st.session_state.recipe_result is not None

# 2. DANACH: Optischer Abstand
st.markdown("<br>", unsafe_allow_html=True)

# 3. AM ENDE: Die Logik (nur EIN Button-Aufruf)
if st.button(c['ui_create'], use_container_width=True) or params_changed:
    if v_url:
        with st.status(c['ui_wait'].format(ports)) as status:
            t_orig, trans, desc, chef = get_full_video_data(v_url)
            if trans or desc:
                res = generate_smart_recipe(t_orig, chef, trans, desc, c, ports, units)
                if res:
                    st.session_state.recipe_result = res
                    st.session_state.recipe_title = t_orig
                    st.session_state.last_params = current_params # Stand speichern
                    update_global_counter()
                    status.update(label=c['ui_ready'], state="complete")
                    if params_changed: 
                        st.rerun() # Seite neu laden für Update
                else: 
                    st.error("AI Error")
            else: 
                st.error("No Data")

if st.session_state.recipe_result:
    st.divider()
    
    # Videotitel verkleinert
    st.markdown(f"#### 📖 {st.session_state.recipe_title}")
    
    # 1. Rezept in Teile zerlegen
    # Wir nutzen split("###"), um Tabelle und Anleitung zu trennen
    parts = st.session_state.recipe_result.split("###")
    ingredients_table = parts[0]
    instructions = "###" + parts[1] if len(parts) > 1 else ""
    
    clean_buy_text = c['ui_buy'].replace('*', '')
    # Fügt das Emoji vor dem Link in jeder Zeile der Tabelle ein
    web_table = ingredients_table.replace(f"[{clean_buy_text}]", f"🛒 [{clean_buy_text}]")
    
    # Zeigt die Tabelle an (Header kommt automatisch korrekt von der KI)
    st.markdown(web_table)
    
    # 3. Einkaufsliste generieren und den Expander
    shopping_list = []
    for line in ingredients_table.split('\n'):
        if '|' in line and '---' not in line:
            cols = [p.strip() for p in line.split('|') if p.strip()]
            if len(cols) >= 2:
                ignore = ["Amount", "Menge", "Ingredient", "Zutat", "Shop", "Buy", "Quantite", "Miktar"]
                if not any(x.lower() in cols[0].lower() or x.lower() in cols[1].lower() for x in ignore):
                    amount = cols[0]
                    ing = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cols[1])
                    shopping_list.append(f"{amount} {ing}")
    
    if shopping_list:
        label = "🛒 " + ("Click to copy ingredients" if c['iso'] == 'en' else "Zutaten zum Kopieren anzeigen")
        with st.expander(label):
            st.code("\n".join(shopping_list), language="text")
            
    # 4. Die Zubereitung anzeigen
    st.markdown(instructions)
    
    # 5. PDF Download Button
    pdf_output = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title, c)
    if pdf_output is not None:
        st.download_button(
            label=c['ui_dl'],
            data=bytes(pdf_output) if not isinstance(pdf_output, bytes) else pdf_output,
            file_name=f"{clean_for_pdf(st.session_state.recipe_title)}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.error("The PDF could not be generated.")

# --- FEEDBACK FORMULAR BLEIBT UNTEN ---
st.divider()
st.subheader(c['fb_header'])
with st.form("fb"):
    txt = st.text_area(c['fb_place']); mail = st.text_input(c['fb_mail'])
    if st.form_submit_button(c['fb_btn']):
        with open("user_feedback.txt", "a") as f: f.write(f"[{selected_lang}] {mail}: {txt}\n---\n")
        st.success(c['fb_thx'])











