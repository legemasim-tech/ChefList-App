import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF

# --- 1. KONFIGURATION & API ---
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    amazon_tag = "cheflist21-21" 
    paypal_email = "legemasim@gmail.com"
except:
    st.error("Bitte Konfiguration in den Secrets prüfen!")
    st.stop()

pay_link_90c = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Rezept_Erstellung&amount=0.90&currency_code=EUR"

client = openai.OpenAI(api_key=api_key)

# --- 2. HILFSFUNKTIONEN ---
def get_full_video_data(video_url):
    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'writesubtitles': True, 'writeautomaticsub': True, 'subtitleslangs': ['de', 'en']}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        video_title = info.get('title', 'Rezept')
        description = info.get('description', '') 
        subs = info.get('subtitles') or info.get('automatic_captions')
        transcript = ""
        if subs:
            target_url = None
            for lang in ['de', 'de-orig', 'en', 'en-orig']:
                if lang in subs:
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
    Du bist ein Profi-Koch. Analysiere das Transkript UND die Videobeschreibung.
    Erstelle das Rezept für {portions} Person(en) im System {unit_instruction}.
    
    WICHTIG FÜR DIE LINKS:
    Nutze NUR: https://www.amazon.de/s?k=[ZUTATENNAME]&tag={tag}
    Link-Text: '🛒 Auf Amazon prüfen*'
    
    Inhalt: Dauer, Schwierigkeit, Backtemperatur, Personenanzahl, Mengen-Tabelle, Zubereitung.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input[:16000]}]
        )
        return response.choices[0].message.content
    except: return None

# --- 3. PDF GENERATOR ---
def create_pdf(text_content, recipe_title):
    pdf = FPDF()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    
    display_title = recipe_title if len(recipe_title) <= 40 else recipe_title[:37] + "..."
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font("Arial", style="B", size=14)
    pdf_header = f"Rezept: {display_title}"
    try:
        safe_header = pdf_header.encode('latin-1', 'replace').decode('latin-1')
    except:
        safe_header = "Dein Rezept"
    
    pdf.cell(190, 15, txt=safe_header, ln=True, align='C', fill=True)
    pdf.ln(5)
    
    lines = text_content.split('\n')
    is_instruction = False
    for line in lines:
        line = line.strip()
        if not line or '---' in line: continue
        if 'Zubereitung' in line:
            is_instruction = True
            pdf.ln(5)
            pdf.set_font("Arial", style="B", size=12)
            pdf.cell(0, 10, txt="Zubereitung:", ln=True)
            continue
        
        headers = ['Dauer:', 'Schwierigkeit:', 'Backtemperatur:', 'Personen:', 'Einheiten:']
        if any(line.startswith(h) for h in headers):
            pdf.set_font("Arial", style="B", size=11)
            pdf.cell(0, 8, txt=line.encode('latin-1', 'replace').decode('latin-1'), ln=True)
            continue

        pdf.set_x(10)
        if '|' in line and not is_instruction:
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2 and ("Menge" in parts[0] or "Zutat" in parts[1]):
                pdf.set_font("Arial", style="B", size=10)
                content = "MENGE - ZUTAT"
            elif len(parts) >= 2:
                pdf.set_font("Arial", size=11)
                content = f"[  ] {parts[0].replace('*','')} {parts[1].replace('*','')}"
            else: continue
            try:
                safe_text = content.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(190, 8, txt=safe_text, ln=True)
                pdf.set_draw_color(220, 220, 220)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            except: continue
        else:
            pdf.set_font("Arial", size=10)
            clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line).replace('*', '')
            try:
                safe_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(190, 7, txt=safe_text, align='L')
                if is_instruction: pdf.ln(2)
            except: continue

    # DER TEAM-GRUSS AM ENDE
    pdf.ln(10)
    pdf.set_font("Arial", style="I", size=10)
    pdf.cell(0, 10, txt="Guten Appetit wuenscht das Team von ChefList Pro!", ln=True, align='C')
    
    return bytes(pdf.output())

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲", layout="centered")

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

with st.sidebar:
    st.title("🍳 ChefList Pro")
    st.info(f"Erstellte Rezepte: {st.session_state.counter}")
    st.markdown("### 💎 Support & Premium")
    st.markdown(f'''<a href="{pay_link_90c}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold;">⚡ Rezept-Erstellung unterstützen (0,90€)</button></a>''', unsafe_allow_html=True)
    st.markdown("---")
    with st.expander("ℹ️ Über & Rechtliches"):
        st.caption("**Betreiber:** Markus Simmel")
        st.caption("**Kontakt:** legemasim@gmail.com")
        st.divider()
        st.caption("✨ Als Amazon-Partner verdiene ich an qualifizierten Verkäufen.")
        st.divider()
        st.caption("🛡️ Wir speichern keine persönlichen Daten.")

st.title("🍲 ChefList Pro")

if st.session_state.counter >= 3:
    st.warning("Limit erreicht. Bitte unterstütze uns mit 0,90€ für weitere Rezepte!")

video_url = st.text_input("YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")
col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    portions = st.slider("Portionen:", 1, 10, 4)
with col_opt2:
    unit_system = st.radio("Einheitensystem:", ["Metrisch (g/ml)", "US-Einheiten (cups/oz)"], horizontal=True)

if st.button("Rezept jetzt erstellen ✨", use_container_width=True):
    if video_url:
        with st.status(f"Wir berechnen dein Rezept...", expanded=True) as status:
            title, transcript, description = get_full_video_data(video_url)
            st.session_state.recipe_title = title
            if transcript or description:
                result = generate_smart_recipe(transcript, description, amazon_tag, portions, unit_system)
                st.session_state.recipe_result = result
                st.session_state.counter += 1
                status.update(label="Dein Rezept ist fertig!", state="complete", expanded=False)
            else:
                st.error("Datenfehler.")

if st.session_state.recipe_result:
    st.divider()
    st.subheader(f"📖 {st.session_state.recipe_title}")
    st.markdown(st.session_state.recipe_result)
    
    st.divider()
    try:
        pdf_data = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title)
        clean_filename = re.sub(r'[^\w\s-]', '', st.session_state.recipe_title[:40]).strip().replace(' ', '_')
        st.download_button(label="📄 PDF Rezept herunterladen", data=pdf_data, file_name=f"ChefList_{clean_filename}.pdf", mime="application/pdf", use_container_width=True)
    except:
        st.error("PDF-Export fehlgeschlagen.")
