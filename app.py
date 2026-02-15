import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF
import os

# --- 1. KONFIGURATION & API ---
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = None

amazon_tag = "cheflist21-21" 
paypal_email = "legemasim@gmail.com"

pay_link_90c = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Rezept_Erstellung&amount=0.90&currency_code=EUR"

if not api_key:
    st.error("Bitte trage deinen OpenAI API Key in die Streamlit Secrets ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- GLOBALER ZÄHLER ---
def update_global_counter():
    file_path = "total_recipes.txt"
    try:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f: f.write("0")
        with open(file_path, "r") as f: count = int(f.read())
        count += 1
        with open(file_path, "w") as f: f.write(str(count))
        return count
    except: return 0

def get_total_count():
    file_path = "total_recipes.txt"
    base_value = 17 # Dein gewünschter Startwert
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f: 
                return int(f.read()) + base_value
        except: return base_value
    return base_value

# --- 2. HILFSFUNKTIONEN ---
def get_full_video_data(video_url):
    try:
        # Wir sagen yt_dlp, dass es nach ALLEN verfügbaren Untertiteln suchen soll ('all')
        ydl_opts = {
            'quiet': True, 
            'skip_download': True, 
            'writesubtitles': True, 
            'writeautomaticsub': True, 
            'subtitleslangs': ['all']  # <--- Geändert: Sucht in jeder Sprache
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        
        video_title = info.get('title', 'Recipe')
        description = info.get('description', '') 
        subs = info.get('subtitles') or info.get('automatic_captions')
        transcript = ""
        
        if subs:
            target_url = None
            # Prioritäten-Liste: 
            # 1. Wir bevorzugen Englisch, falls vorhanden.
            # 2. Wenn nicht, nehmen wir die ERSTE verfügbare Sprache aus der Liste.
            preferred_langs = ['en', 'en-orig', 'en-US', 'de', 'de-orig']
            
            # Erst nach Favoriten suchen
            for lang in preferred_langs:
                if lang in subs:
                    for f in subs[lang]:
                        if f.get('ext') == 'json3':
                            target_url = f.get('url')
                            break
                    if target_url: break
            
            # Wenn kein Favorit gefunden wurde, nimm einfach IRGENDWELCHE Untertitel
            if not target_url:
                for lang in subs:
                    for f in subs[lang]:
                        if f.get('ext') == 'json3':
                            target_url = f.get('url')
                            break
                    if target_url: break

            if target_url:
                res = requests.get(target_url)
                if 'json3' in target_url:
                    data = res.json()
                    transcript = " ".join([seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])
        
        return video_title, transcript, description
    except:
        return "Rezept", None, None
        
def generate_smart_recipe(transcript, description, tag, portions, unit_system):
    combined_input = f"VIDEOTITEL:\n{transcript}\n\nINFOTEXT/BESCHREIBUNG:\n{description}"
    unit_instruction = "METRISCH (g/ml)" if unit_system == "Metrisch (g/ml)" else "US-Einheiten (cups/oz)"
    
    system_prompt = f"""
    Du bist ein Profi-Koch und ein extrem präziser Mathematiker.
    
    DEINE WICHTIGSTE REGEL: 
    1. Identifiziere für wie viele Personen das Originalrezept im Video ist (meist 2 oder 4).
    2. Berechne alle Mengen EXAKT auf genau {portions} Person(en) um. 
    3. Die Zahlen in deiner Tabelle MÜSSEN sich proportional zur Portionszahl {portions} ändern. Überprüfe deine Rechnung doppelt!
    
    STRUKTUR:
    1. Eckdaten (Dauer, Schwierigkeit, Personenanzahl: {portions})
    2. Mengen-Tabelle (Spalten: Menge | Zutat | Kaufen)
       -> JEDE Zutat braucht in der Spalte 'Kaufen' diesen Link: https://www.amazon.de/s?k=[ZUTATENNAME]&tag={tag}
       -> Link-Text: '🛒 Auf Amazon kaufen*'
    3. Zubereitung (Schritt-für-Schritt, Mengen auch hier an {portions} Personen anpassen!)
    
    WICHTIG: Nutze für das System {unit_instruction}. Wenn US-Einheiten gewählt sind, schreibe IMMER die Einheit hinter die Zahl.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input[:16000]}]
        )
        return response.choices[0].message.content
    except: return None

# --- 3. PDF GENERATOR ---
def clean_for_pdf(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'Euro'}
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    return text

def create_pdf(text_content, recipe_title):
    pdf = FPDF()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font("Arial", style="B", size=14)
    
    display_title = clean_for_pdf(recipe_title if len(recipe_title) <= 40 else recipe_title[:37] + "...")
    pdf.cell(190, 15, txt=f"Rezept: {display_title}", ln=True, align='C', fill=True)
    pdf.ln(5)
    
    lines = text_content.split('\n')
    is_instruction = False
    for line in lines:
        line = line.strip()
        if not line or '---' in line: continue
        line = clean_for_pdf(line)
        
        if 'Zubereitung' in line:
            is_instruction = True
            pdf.ln(5)
            pdf.set_font("Arial", style="B", size=12)
            pdf.cell(0, 10, txt="Zubereitung:", ln=True)
            continue
            
        headers = ['Dauer:', 'Schwierigkeit:', 'Backtemperatur:', 'Personen:', 'Einheiten:']
        if any(line.startswith(h) for h in headers):
            pdf.set_font("Arial", style="B", size=11)
            pdf.cell(0, 8, txt=line, ln=True)
            continue
            
        pdf.set_x(10)
        if '|' in line and not is_instruction:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                if "Menge" in parts[0] or "Zutat" in parts[1]:
                    pdf.set_font("Arial", style="B", size=10)
                    content = "MENGE - ZUTAT"
                else:
                    pdf.set_font("Arial", style="B", size=11)
                    content = f"[  ] {parts[0].replace('*','')} {parts[1].replace('*','')}"
                
                pdf.cell(190, 8, txt=content, ln=True)
                pdf.set_draw_color(220, 220, 220)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        else:
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(190, 7, txt=line.replace('*', ''), align='L')
            if is_instruction: pdf.ln(2)
            
    pdf.ln(10)
    pdf.set_font("Arial", style="I", size=10)
    pdf.cell(0, 10, txt="Guten Appetit wuenscht das Team von ChefList Pro!", ln=True, align='C')
    return bytes(pdf.output())

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲", layout="centered")

st.markdown("""
    <style>
        [data-testid="stSidebar"] img {
            background-color: white;
            padding: 10px;
            border-radius: 12px;
            border: 2px solid #e0e0e0;
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.title("🍳 ChefList Pro")
        
    st.info(f"Deine erstellten Rezepte: {st.session_state.counter}")
    
    # Dein bestehender deutscher Support-Button
    st.markdown(f'''<a href="{pay_link_90c}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold;">⚡ ChefList Pro unterstützen (0,90€)</button></a>''', unsafe_allow_html=True)
    
    # NEU: Kleiner Hinweis-Link zur englischen Version
    st.markdown('<p style="text-align: center; font-size: 0.8em; margin-top: 10px;"><a href="https://cheflist-app-en.streamlit.app/" target="_blank">Switch to English Version</a></p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.expander("ℹ️ Über & Rechtliches"):
        st.caption("**Betreiber:** Markus Simmel\n\n**Kontakt:** legemasim@gmail.com")
        st.divider()
        st.write(f"📊 Bereits generierte Rezepte: **{get_total_count()}**")
        st.divider()
        st.caption("✨ Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.")
        st.divider()
        st.subheader("🛡️ Datenschutz & Sicherheit")
        st.caption("Wir speichern keine persönlichen Daten. Die Verarbeitung erfolgt verschlüsselt.")
        st.divider()
        st.caption("⚠️ **Hinweis:** Diese App nutzt eine KI. KI kann Fehler machen – bitte prüfe die Angaben (z.B. Backzeiten) vor dem Kochen.")

st.title("🍲 ChefList Pro")

if st.session_state.counter >= 3:
    st.warning("Du hast 3 Rezepte erstellt. Bitte unterstütze uns mit 0,90€!")

video_url = st.text_input("YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")
col_opt1, col_opt2 = st.columns(2)
portions = col_opt1.slider("Portionen:", 1, 10, 4)
unit_system = col_opt2.radio("Einheitensystem:", ["Metrisch (g/ml)", "US-Einheiten (cups/oz)"], horizontal=True)

if st.button("Rezept jetzt erstellen ✨", use_container_width=True):
    if video_url:
        with st.status(f"Berechne Rezept für {portions} Personen... dies kann ein paar Sekunden dauern.", expanded=True) as status:
            title, transcript, description = get_full_video_data(video_url)
            st.session_state.recipe_title = title
            if transcript or description:
                result = generate_smart_recipe(transcript, description, amazon_tag, portions, unit_system)
                st.session_state.recipe_result = result
                st.session_state.counter += 1
                update_global_counter()
                status.update(label="Bereit!", state="complete", expanded=False)
            else:
                st.error("Keine Daten gefunden.")

if st.session_state.recipe_result:
    st.divider()
    st.subheader(f"📖 {st.session_state.recipe_title}")
    st.markdown(st.session_state.recipe_result.replace("Auf Amazon prüfen", "Auf Amazon kaufen"))
    
    st.divider()
    try:
        pdf_data = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title)
        clean_filename = re.sub(r'[^\w\s-]', '', st.session_state.recipe_title[:40]).strip().replace(' ', '_')
        st.download_button("📄 PDF Rezept herunterladen", pdf_data, file_name=f"ChefList_{clean_filename}.pdf", mime="application/pdf", use_container_width=True)
    except:
        st.error("Fehler beim PDF-Export.")



