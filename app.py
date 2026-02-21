import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. INTERNATIONALE KONFIGURATION ---
LANG_CONFIG = {

    "English (US)": {
        "tag": "cheflist21-20", "amz": "amazon.com", "curr": "USD", "iso": "en",
        "ui_header": "Convert YouTube recipes into printable PDFs",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Servings:", "ui_units": "Units:", 
        "ui_unit_opts": ["US (cups/oz/°F)", "Metric (g/ml/°C)"],
        "ui_create": "Create Recipe ✨", "ui_wait": "Calculated by the chef... just a moment! 👨‍🍳", "ui_ready": "Ready!",
        "ui_dl": "📄 Download PDF Recipe", "ui_buy": "Buy on Amazon*", "ui_table_header": "Shop Ingredients",
        "ui_btn_pay": "⚡ Support ChefList Pro ($0.90)",
        "ai_lang": "AMERICAN ENGLISH", 
        "ui_counter_text": "Recipes created:", 
        "legal_title": "About & Legal", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Total recipes:", 
        "legal_amz": "✨ As an Amazon Associate, I earn from qualifying purchases.", 
        "legal_privacy_title": "🛡️ Data Protection", 
        "legal_privacy_body": "We do not store personal data. Processing is encrypted.", 
        "legal_note": "⚠️ **Note:** This app uses AI. AI can make mistakes – please check details before cooking.",
        "fb_header": "Help us improve! 🍲", "fb_btn": "Send ✨", 
        "fb_place": "What can we do better?", "fb_mail": "Email (optional)", "fb_thx": "Saved! 🙌",
        "pdf_rec": "Recipe", "pdf_instr": "Instructions", 
        "pdf_enjoy": "Happy cooking from the Cheflist Pro Team!",
        "pdf_video_link": "Recipe from the video:"
    },
    "English (UK)": {
        "tag": "cheflist-uk-21", "amz": "amazon.co.uk", "curr": "GBP", "iso": "en-GB",
        "ui_header": "Convert YouTube recipes into printable PDFs",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Servings:", "ui_units": "Units:", 
        "ui_unit_opts": ["Metric (g/ml/°C)", "US (cups/oz/°F)"],
        "ui_create": "Create Recipe ✨", 
        "ui_wait": "Calculated by the chef... just a moment! 👨‍🍳", 
        "ui_ready": "Ready!",
        "ui_dl": "📄 Download PDF Recipe", "ui_buy": "Buy on Amazon*", "ui_table_header": "Shop Ingredients",
        "ui_btn_pay": "⚡ Support ChefList Pro (£0.80)",
        "ai_lang": "BRITISH ENGLISH",
        "ui_counter_text": "Recipes created:", 
        "legal_title": "About & Legal", 
        "legal_op": "**Operator:** Markus Simmel", 
        "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Total recipes:", 
        "legal_amz": "✨ As an Amazon Associate, I earn from qualifying purchases.", 
        "legal_privacy_title": "🛡️ Data Protection", 
        "legal_privacy_body": "We do not store personal data. Processing is encrypted.", 
        "legal_note": "⚠️ **Note:** This app uses AI. AI can make mistakes – please check details before cooking.",
        "fb_header": "Help us improve! 🍲", "fb_btn": "Send ✨", 
        "fb_place": "What can we do better?", "fb_mail": "Email (optional)", "fb_thx": "Saved! 🙌",
        "pdf_rec": "Recipe", "pdf_instr": "Instructions", 
        "pdf_enjoy": "Happy cooking from the Cheflist Pro Team!",
        "pdf_video_link": "Recipe from the video:"
    },
    "Deutsch": {
        "tag": "cheflist21-21", "amz": "amazon.de", "curr": "EUR", "iso": "de",
        "ui_header": "YouTube-Rezepte in druckbare PDFs verwandeln",
        "ui_input_label": "YouTube Video URL:",
        "ui_servings": "Portionen:", "ui_units": "Einheiten:", 
        "ui_unit_opts": ["Metrisch (g/ml)", "US-Einheiten (cups/oz)"],
        "ui_create": "Rezept erstellen ✨", "ui_wait": "Der Chefkoch rechnet kurz nach... einen Augenblick! 👨‍🍳", "ui_ready": "Bereit!",
        "ui_dl": "📄 PDF herunterladen", "ui_buy": "Auf Amazon kaufen*", "ui_table_header": "Zutaten einkaufen",
        "ui_btn_pay": "⚡ ChefList Pro unterstützen (0,90€)",
        "ui_counter_text": "Erstellte Rezepte:", 
        "legal_title": "Über & Rechtliches", "legal_op": "**Betreiber:** Markus Simmel", "legal_contact": "**Kontakt:** legemasim@gmail.com",
        "legal_total": "Gesamt Rezepte:", 
        "legal_amz": "✨ Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.", 
        "legal_privacy_title": "🛡️ Datenschutz", 
        "legal_privacy_body": "Wir speichern keine persönlichen Daten. Die Verarbeitung erfolgt verschlüsselt.", 
        "legal_note": "⚠️ **Hinweis:** Diese App nutzt eine KI. KI kann Fehler machen – bitte prüfe die Angaben vor dem Kochen.",
        "ai_lang": "GERMAN", 
        "fb_header": "Hilf uns besser zu werden! 🍲", "fb_btn": "Senden ✨",
        "fb_place": "Was können wir besser machen?", "fb_mail": "E-Mail (optional)", "fb_thx": "Gespeichert! 🙌",
        "pdf_rec": "Rezept", "pdf_instr": "Zubereitung", 
        "pdf_enjoy": "Gutes Gelingen wünscht das Team von Cheflist Pro.",
        "pdf_video_link": "Rezept aus dem Video:"
    },
    "Español": {
        "tag": "cheflist21-20", "amz": "amazon.es", "curr": "EUR", "iso": "es",
        "ui_header": "YouTube a PDF", "ui_input_label": "URL del video:",
        "ui_servings": "Porciones:", "ui_units": "Unidades:", "ui_unit_opts": ["Métrico (g/ml)", "EE.UU. (cups/oz)"],
        "ui_create": "Crear ✨", "ui_wait": "El chef está calculando... ¡un momento! 🥘", "ui_ready": "¡Listo!",
        "ui_dl": "📄 Descargar PDF", "ui_buy": "Comprar en Amazon*", "ui_table_header": "Comprar ingredientes",
        "ui_btn_pay": "⚡ Apoyar ChefList Pro (0,90€)",
        "ui_counter_text": "Recetas:", 
        "legal_title": "Info Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contacto:** legemasim@gmail.com",
        "legal_total": "Total recetas:", 
        "legal_amz": "✨ Como asociado de Amazon, gano por las compras calificadas.", 
        "legal_privacy_title": "🛡️ Privacidad", 
        "legal_privacy_body": "No almacenamos datos personales.", 
        "legal_note": "⚠️ **Nota:** Esta aplicación utiliza IA. Verifique los detalles antes de cocinar.",
        "ai_lang": "SPANISH", "fb_header": "¡Ayúdanos! 🍲", "fb_btn": "Enviar ✨",
        "fb_place": "¿Ideas?", "fb_mail": "Correo", "fb_thx": "¡Gracias! 🙌",
        "pdf_rec": "Receta", "pdf_instr": "Instrucciones", 
        "pdf_enjoy": "¡El equipo de Cheflist Pro le desea mucho éxito!",
        "pdf_video_link": "Receta del video:"
    },
    "Français": {
        "tag": "cheflist21-20", "amz": "amazon.fr", "curr": "EUR", "iso": "fr",
        "ui_header": "YouTube en PDF", "ui_input_label": "URL vidéo:",
        "ui_servings": "Portions:", "ui_units": "Unités:", "ui_unit_opts": ["Métrique (g/ml)", "US (cups/oz)"],
        "ui_create": "Créer ✨", "ui_wait": "Le chef prépare tout... un instant ! 🍳", "ui_ready": "Prêt!",
        "ui_dl": "📄 Télécharger le PDF", "ui_buy": "Acheter sur Amazon*", "ui_table_header": "Acheter les ingrédients",
        "ui_btn_pay": "⚡ Soutenir ChefList Pro (0,90€)",
        "ui_counter_text": "Recettes:", 
        "legal_title": "Mentions Légales", "legal_op": "**Opérateur:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Total recettes:", 
        "legal_amz": "✨ En tant que partenaire Amazon, je réalise un bénéfice.", 
        "legal_privacy_title": "🛡️ Confidentialité", 
        "legal_privacy_body": "Nous ne stockons pas de données personnelles.", 
        "legal_note": "⚠️ **Remarque:** Cette application utilise l'IA. Veuillez vérifier les détails.",
        "ai_lang": "FRENCH", "fb_header": "Aidez-nous! 🍲", "fb_btn": "Envoyer ✨",
        "fb_place": "Idées?", "fb_mail": "Email", "fb_thx": "Merci! 🙌",
        "pdf_rec": "Recette", "pdf_instr": "Instructions", 
        "pdf_enjoy": "L'équipe de Cheflist Pro vous souhaite une bonne réussite !",
        "pdf_video_link": "Recette de la vidéo :"
    },
    "Italiano": {
        "tag": "cheflist21-20", "amz": "amazon.it", "curr": "EUR", "iso": "it",
        "ui_header": "YouTube in PDF", "ui_input_label": "URL video:",
        "ui_servings": "Porzioni:", "ui_units": "Unità:", "ui_unit_opts": ["Metrico (g/ml)", "US (cups/oz)"],
        "ui_create": "Crea ✨", "ui_wait": "Lo chef sta calcolando... solo un attimo! 🍝", "ui_ready": "Pronto!",
        "ui_dl": "📄 Scarica PDF", "ui_buy": "Acquista su Amazon*", "ui_table_header": "Acquista ingredienti",
        "ui_btn_pay": "⚡ Sostieni ChefList Pro (0,90€)",
        "ui_counter_text": "Ricette:", 
        "legal_title": "Info Legali", "legal_op": "**Operatore:** Markus Simmel", "legal_contact": "**Contatto:** legemasim@gmail.com",
        "legal_total": "Totale ricette:", 
        "legal_amz": "✨ In qualità di Affiliato Amazon, ricevo un guadagno.", 
        "legal_privacy_title": "🛡️ Privacy", 
        "legal_privacy_body": "Non memorizziamo dati personali.", 
        "legal_note": "⚠️ **Nota:** Questa app utilizza l'IA. Controlla i dettagli prima di cucinare.",
        "ai_lang": "ITALIAN", "fb_header": "Aiutaci! 🍲", "fb_btn": "Invia ✨",
        "fb_place": "Idee?", "fb_mail": "Email", "fb_thx": "Grazie! 🙌",
        "pdf_rec": "Ricetta", "pdf_instr": "Istruzioni", 
        "pdf_enjoy": "Buona fortuna dal team di Cheflist Pro!",
        "pdf_video_link": "Ricetta dal video:"
    },
    "Português": {
        "tag": "cheflist21-20", "amz": "amazon.es", "curr": "EUR", "iso": "pt",
        "ui_header": "Converter YouTube em PDF", 
        "ui_input_label": "URL do vídeo:",
        "ui_servings": "Doses:", "ui_units": "Unidades:", 
        "ui_unit_opts": ["Métrico (g/ml)", "Imperial (cups/oz)"],
        "ui_create": "Criar ✨", "ui_wait": "O chef está a preparar... um momento! 🥣", "ui_ready": "Pronto!",
        "ui_dl": "📄 Descarregar PDF", "ui_buy": "Comprar na Amazon*", "ui_table_header": "Comprar ingredientes",
        "ui_btn_pay": "⚡ Apoiar ChefList Pro (0,90€)",
        "ui_counter_text": "Receitas:", 
        "legal_title": "Sobre & Legal", "legal_op": "**Operador:** Markus Simmel", "legal_contact": "**Contacto:** legemasim@gmail.com",
        "legal_total": "Total:", 
        "legal_amz": "✨ Como associado da Amazon, ganho com compras qualificadas.", 
        "legal_privacy_title": "🛡️ Privacidade", 
        "legal_privacy_body": "Não guardamos dados pessoais.", 
        "legal_note": "⚠️ **Nota:** Esta aplicação usa IA. Verifique os detalhes.",
        "ai_lang": "PORTUGUESE", "fb_header": "Ajude! 🍲", "fb_btn": "Enviar ✨",
        "fb_place": "Ideias?", "fb_mail": "Email", "fb_thx": "Obrigado! 🙌",
        "pdf_rec": "Receita", "pdf_instr": "Instruções", 
        "pdf_enjoy": "Bom proveito da equipa ChefList Pro!",
        "pdf_video_link": "Receita do vídeo:"
    },
    "Nederlands": {
        "tag": "cheflist21-20", "amz": "amazon.nl", "curr": "EUR", "iso": "nl",
        "ui_header": "YouTube naar PDF", "ui_input_label": "Video URL:",
        "ui_servings": "Porties:", "ui_units": "Eenheden:", "ui_unit_opts": ["Metrisch (g/ml)", "US (cups/oz)"],
        "ui_create": "Maken ✨", "ui_wait": "De chef berekent alles... een ogenblik! ⏲️", "ui_ready": "Klaar!",
        "ui_dl": "📄 PDF downloaden", "ui_buy": "Koop op Amazon*", "ui_table_header": "Ingrediënten kopen",
        "ui_btn_pay": "⚡ ChefList Pro steunen (0,90€)",
        "ui_counter_text": "Recepten:",
        "legal_title": "Juridisch", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Contact:** legemasim@gmail.com",
        "legal_total": "Totaal:", 
        "legal_amz": "✨ Als Amazon-partner verdien ik aan aankopen.", 
        "legal_privacy_title": "🛡️ Privacy", 
        "legal_privacy_body": "Wij slaan geen persoonlijke gegevens op.", 
        "legal_note": "⚠️ **Let op:** Deze app maakt gebruik van AI. Controleer de details.",
        "ai_lang": "DUTCH", "fb_header": "Help ons! 🍲", "fb_btn": "Verzenden ✨",
        "fb_place": "Ideeën?", "fb_mail": "Email", "fb_thx": "Bedankt! 🙌",
        "pdf_rec": "Recept", "pdf_instr": "Instructies", 
        "pdf_enjoy": "Veel succes gewenst door het Cheflist Pro team.",
        "pdf_video_link": "Recept uit de video:"
    },
    "Polski": {
        "tag": "cheflist21-20", "amz": "amazon.pl", "curr": "PLN", "iso": "pl",
        "ui_header": "YouTube na PDF", "ui_input_label": "URL filmu:",
        "ui_servings": "Porcje:", "ui_units": "Jednostki:", "ui_unit_opts": ["Metryczne (g/ml)", "US (cups/oz)"],
        "ui_create": "Utwórz ✨", "ui_wait": "Szef kuchni oblicza... jeszcze chwila! 🥟", "ui_ready": "Gotowe!",
        "ui_dl": "📄 Pobierz PDF", "ui_buy": "Kup na Amazon*", "ui_table_header": "Kup składniki",
        "ui_btn_pay": "⚡ Wesprzyj ChefList Pro (4 PLN)",
        "ui_counter_text": "Przepisy:", 
        "legal_title": "Prawne", "legal_op": "**Operator:** Markus Simmel", "legal_contact": "**Kontakt:** legemasim@gmail.com",
        "legal_total": "Suma:", 
        "legal_amz": "✨ Jako partner Amazon zarabiam na zakupach.", 
        "legal_privacy_title": "🛡️ Prywatność", 
        "legal_privacy_body": "Nie przechowujemy danych osobowych.", 
        "legal_note": "⚠️ **Uwaga:** Ta aplikacja korzysta z AI. Sprawdź szczegóły.",
        "ai_lang": "POLISH", "fb_header": "Pomoc! 🍲", "fb_btn": "Wyślij ✨",
        "fb_place": "Pomysły?", "fb_mail": "Email", "fb_thx": "Dzięki! 🙌",
        "pdf_rec": "Przepis", "pdf_instr": "Instrukcje", 
        "pdf_enjoy": "Powodzenia życzy zespół Cheflist Pro.",
        "pdf_video_link": "Przepis z filmu:"
    },
    "Türkçe": {
        "tag": "cheflist21-20", "amz": "amazon.com.tr", "curr": "TRY", "iso": "tr",
        "ui_header": "YouTube'dan PDF'e", "ui_input_label": "Video URL:",
        "ui_servings": "Porsiyon:", "ui_units": "Birimler:", "ui_unit_opts": ["Metrik (g/ml)", "ABD (cups/oz)"],
        "ui_create": "Oluştur ✨", "ui_wait": "Şef hesaplıyor... çok kısa bir süre! 🥘", "ui_ready": "Hazır!",
        "ui_dl": "📄 PDF İndir", "ui_buy": "Amazon'dan al*", "ui_table_header": "Malzemeleri satın al",
        "ui_btn_pay": "⚡ ChefList Pro'yu Destekle (30 TL)",
        "ui_counter_text": "Tarifler:", 
        "legal_title": "Yasal", "legal_op": "**Operatör:** Markus Simmel", "legal_contact": "**İletişim:** legemasim@gmail.com",
        "legal_total": "Toplam:", 
        "legal_amz": "✨ Bir Amazon ortağı olarak kazanç sağlıyorum.", 
        "legal_privacy_title": "🛡️ Veri", 
        "legal_privacy_body": "Kişisel verileri saklamıyoruz.", 
        "legal_note": "⚠️ **Not:** Bu uygulama AI kullanır. Lütfen kontrol edin.",
        "ai_lang": "TURKISH", "fb_header": "Yardım! 🍲", "fb_btn": "Gönder ✨",
        "fb_place": "Fikirler?", "fb_mail": "E-posta", "fb_thx": "Teşekkürler! 🙌",
        "pdf_rec": "Tarif", "pdf_instr": "Talimatlar", 
        "pdf_enjoy": "Cheflist Pro ekibi başarılar diler.",
        "pdf_video_link": "Videodaki tarif:"
    },
    "日本語": {
        "tag": "cheflist21-20", "amz": "amazon.co.jp", "curr": "JPY", "iso": "ja",
        "ui_header": "YouTubeをPDFに", "ui_input_label": "動画URL:",
        "ui_servings": "人数:", "ui_units": "単位:", "ui_unit_opts": ["メートル法 (g/ml)", "US単位 (cups/oz)"],
        "ui_create": "作成 ✨", "ui_wait": "シェフが計算中... 少々お待ちください 🍱", "ui_ready": "完了！",
        "ui_dl": "📄 PDF保存", "ui_buy": "Amazonで購入*", "ui_table_header": "材料を購入する",
        "ui_btn_pay": "⚡ ChefList Proを支援 (¥140)",
        "ui_counter_text": "レシピ数:", 
        "legal_title": "法的情報", "legal_op": "**運営者:** Markus Simmel", "legal_contact": "**連絡先:** legemasim@gmail.com",
        "legal_total": "累計:", 
        "legal_amz": "✨ Amazonアソシエイトとして収入を得ています。", 
        "legal_privacy_title": "🛡️ 保護", 
        "legal_privacy_body": "個人データは保存されません。", 
        "legal_note": "⚠️ **注意:** このアプリはAIを使用しています。調理前に確認してください。",
        "ai_lang": "JAPANESE", "fb_header": "改善にご協力ください！ 🍲", "fb_btn": "送信 ✨",
        "fb_place": "ご意見", "fb_mail": "メール", "fb_thx": "感謝! 🙌",
        "pdf_rec": "Recipe", "pdf_instr": "Instructions", 
        "pdf_enjoy": "Cheflist Proチームより、幸運を祈ります！",
        "pdf_video_link": "動画のレシピ:"
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

def generate_smart_recipe(video_title, channel_name, transcript, description, config, unit_system):
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
    
    # Spezifische Anweisung für UK vs US
    temp_instruction = ""
    if "UK" in config['ai_lang'] or "BRITISH" in config['ai_lang']:
        temp_instruction = "For oven temperatures, provide Celsius and mention Gas Mark if applicable."
    else:
        temp_instruction = "For US units, always convert Celsius to Fahrenheit."

    # VERBESSERTER SYSTEM PROMPT
    system_prompt = f"""
    You are a professional chef. Respond in {config['ai_lang']}.
    TARGET UNITS: {u_inst}

    ### CORE TASK:
    1. TITLE: Create a catchy, professional recipe title in {config['ai_lang']} based on the video.
    2. EXTRACT: Get the exact recipe from the transcript/description.
    3. CONVERT: Keep original proportions but convert all measurements to {u_inst}. 
       IMPORTANT: Convert oven temperatures (Celsius to Fahrenheit for US, or vice-versa).
    4. NO SCALING: Keep the recipe exactly as intended by the chef (original servings).
    
    ### STRUCTURE:
    # [Catchy Recipe Title]

    ### Ingredients
    | {h_amount} | {h_ingredient} | {table_header} |
    |---|---|---|
    ...
    
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
    7. Convert all measurements to {unit_system}. 
       IMPORTANT: This includes oven temperatures (e.g., Celsius to Fahrenheit for US, or vice versa).
    8. Keep the original cooking times.
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

def create_pdf(text_content, recipe_title, video_url, channel_name, config):
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
        safe_title = clean_for_pdf(recipe_title[:45])
        pdf.cell(150, 15, txt=f"{safe_title}", ln=True, align='L', fill=True)
        
        # --- NEU: KANALNAME / KOCH ---
        pdf.set_font("Arial", style="I", size=11)
        pdf.set_text_color(100, 100, 100) # Grau für eine edle Optik
        pdf.cell(0, 8, txt=f"by {clean_for_pdf(channel_name)}", ln=True)
        
        # --- NEU: YOUTUBE LINK MIT ICON ---
        pdf.ln(2)
        pdf.set_font("Arial", style="B", size=10)
        
        # Rotes Icon simulieren (oder Bild einfügen)
        pdf.set_fill_color(255, 0, 0) # YouTube Rot
        pdf.set_text_color(255, 255, 255) # Weißer Text für das "Play" Symbol
        pdf.cell(10, 6, txt=" > ", ln=0, align='C', fill=True) 
        
        # Label und Link
        pdf.set_text_color(0, 0, 0) # Zurück zu Schwarz
        pdf.set_font("Arial", size=10)
        link_label = f" {config.get('pdf_video_link', 'Video:')} "
        pdf.cell(pdf.get_string_width(link_label), 6, txt=link_label, ln=0)
        
        # Der eigentliche Link in Blau
        pdf.set_text_color(0, 0, 255)
        pdf.cell(0, 6, txt=video_url, ln=True, link=video_url)
        
        pdf.set_text_color(0, 0, 0) # Reset
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
                    # Header erkennen
                    if any(x in parts[0] for x in ["Amount", "Menge", "Ingredient", "Zutat", "Quantite"]):
                        pdf.set_font("Arial", style="B", size=10)
                        pdf.set_fill_color(240, 240, 240)
                        content = f"{parts[0].upper()} - {parts[1].upper()}"
                    else:
                        pdf.set_font("Arial", size=11)
                        # Säubern von Markdown-Links für das PDF
                        clean_amount = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', parts[0]).replace('*','')
                        clean_ingred = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', parts[1]).replace('*','')
                        content = f"{clean_amount} {clean_ingred}"
                    
                    pdf.cell(0, 8, txt=clean_for_pdf(content), ln=True)
                    pdf.set_draw_color(200, 200, 200)
                    pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y())
            
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
        
        # 'S' steht für 'String', wird aber von Streamlit als Byte-Stream benötigt
        pdf_bytes = pdf.output(dest='S') 
        
        # Falls es noch ein String ist, in Bytes umwandeln
        if isinstance(pdf_bytes, str):
            pdf_bytes = pdf_bytes.encode('latin1')
            
        return pdf_bytes

    except Exception as e:
        print(f"PDF Debug: {e}")
        return None
        
# --- 5. INTERFACE ---
st.set_page_config(page_title="ChefList Pro Global", page_icon="👨‍🍳")
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

    [data-testid="stSidebar"] .stExpander summary p {
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] .stExpander .stRadio label p {
        font-size: 0.8rem !important;
        line-height: 1.2 !important;
    }
    [data-testid="stSidebar"] .stExpander div[role="radiogroup"] {
        gap: 5px !important;
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
if "recipe_chef" not in st.session_state: st.session_state.recipe_chef = ""
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

st.title("👨‍🍳 ChefList Pro")
st.subheader(c['ui_header'])

v_url = st.text_input(c['ui_input_label'], placeholder="https://...")

# --- OPTISCH SCHÖNE EINGABE ---
col_left, col_mid, col_right = st.columns([1, 2, 1])

with col_mid:
    units = st.radio(
        f"⚖️ {c['ui_units']}", 
        c['ui_unit_opts'], 
        horizontal=True,
        label_visibility="visible"
    )

# Parameter-Logik
current_params = {"url": v_url, "units": units}
params_changed = current_params != st.session_state.last_params and st.session_state.recipe_result is not None

st.markdown("<br>", unsafe_allow_html=True)

if st.button(c['ui_create'], use_container_width=True):
    if v_url:
        wait_msg = c['ui_wait'].split('{0}')[0].strip(" .") + "..."
        with st.status(wait_msg) as status:
            t_orig, trans, desc, chef = get_full_video_data(v_url)
            if trans or desc:
                res = generate_smart_recipe(t_orig, chef, trans, desc, c, units)
                if res:
                    # Trenne den von der KI generierten Titel vom Rest des Rezepts
                    raw_parts = res.split('###')
                   # 1. Titel extrahieren
                    st.session_state.recipe_title = raw_parts[0].strip().replace('#', '')
                    
                    # 2. Den Rest des Rezepts (Tabelle + Anleitung) wieder zusammenfügen
                    # Wir behalten die '###' bei, damit das Interface sie später zum Splitten findet
                    recipe_body = ""
                    if len(raw_parts) > 1:
                        recipe_body = "###" + "###".join(raw_parts[1:])
                    
                    st.session_state.recipe_result = recipe_body
                    st.session_state.recipe_chef = chef
                    update_global_counter()
                    
                    status.update(label=c['ui_ready'], state="complete")
                    st.rerun()
                else: st.error("AI Error")
            else: st.error("No Data")

if st.session_state.recipe_result:
    st.divider()
    
    # 1. Titel anzeigen
    st.markdown(f"## 👨‍🍳 {st.session_state.recipe_title}")
    
    # 2. Sektionen trennen
    # Wir splitten bei ### und säubern
    raw_sections = st.session_state.recipe_result.split("###")
    sections = [s.strip() for s in raw_sections if s.strip()]
    
    ingredients_table = ""
    instructions = ""
    
    for section in sections:
        # Eine Tabelle erkennen wir an den Pipes | und mindestens zwei Zeilen
        if section.count('|') > 5: 
            ingredients_table = section
        # Eine Anleitung erkennen wir an Zahlen oder wenn sie nicht die Tabelle ist
        elif len(section) > 10 and not ingredients_table:
            # Falls die KI 'Ingredients' als Text schickt, ignorieren wir das hier
            pass
        elif len(section) > 10:
            instructions += "\n\n### " + section

    # 3. Anzeige Tabelle
    if ingredients_table:
        clean_buy_text = c['ui_buy'].replace('*', '')
        # Wir stellen sicher, dass die Trennzeile |---| existiert, falls die KI sie vergisst
        if "|---|---|" not in ingredients_table and ingredients_table.count('|') > 4:
            lines = ingredients_table.split('\n')
            if len(lines) > 1:
                lines.insert(1, "|---|---|---|")
                ingredients_table = "\n".join(lines)
        
        web_table = ingredients_table.replace(f"[{clean_buy_text}]", f"🛒 [{clean_buy_text}]")
        st.markdown(web_table)
        
        # Einkaufsliste (Expander)
        shopping_list = []
        for line in ingredients_table.split('\n'):
            if '|' in line and not any(x in line for x in ['---', 'Amount', 'Menge', 'Quantite']):
                cols = [p.strip() for p in line.split('|') if p.strip()]
                if len(cols) >= 2:
                    ing = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cols[1])
                    shopping_list.append(f"{cols[0]} {ing}")
        
        if shopping_list:
            with st.expander("🛒 " + (c.get('ui_table_header', 'Ingredients'))):
                st.code("\n".join(shopping_list), language="text")

    # 4. Anzeige Anleitung
    if instructions:
        st.markdown(instructions)

    st.divider()
    # 5. PDF Download
# 5. PDF Download Button
    try:
        pdf_output = create_pdf(
            st.session_state.recipe_result, 
            st.session_state.recipe_title, 
            v_url, 
            st.session_state.recipe_chef, 
            c
        )
        
        if pdf_output:
            # Wir stellen sicher, dass die Daten wirklich Bytes sind
            data_to_download = pdf_output
            
            st.download_button(
                label=c['ui_dl'],
                data=data_to_download,
                file_name=f"{clean_for_pdf(st.session_state.recipe_title)}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="pdf_download_btn" # Eindeutiger Key verhindert Refresh-Fehler
            )
        else:
            st.error("PDF-Inhalt leer.")
    except Exception as e:
        st.error(f"Fehler beim Bereitstellen des PDFs: {e}")

# --- FEEDBACK FORMULAR BLEIBT UNTEN ---
st.divider()
st.subheader(c['fb_header'])
with st.form("fb"):
    txt = st.text_area(c['fb_place']); mail = st.text_input(c['fb_mail'])
    if st.form_submit_button(c['fb_btn']):
        with open("user_feedback.txt", "a") as f: f.write(f"[{selected_lang}] {mail}: {txt}\n---\n")
        st.success(c['fb_thx'])





















