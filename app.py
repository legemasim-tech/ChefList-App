import streamlit as st
import openai
import requests
import re
import yt_dlp
from fpdf import FPDF

# --- 1. KONFIGURATION & API ---
# Wir laden die Daten sicher. Wenn sie fehlen, nutzen wir Platzhalter statt abzustürzen.
api_key = st.secrets.get("OPENAI_API_KEY")
amazon_tag = st.secrets.get("AMAZON_TAG", "cheflist21-21")
paypal_email = "legemasim@gmail.com"

if not api_key:
    st.error("Fehler: OPENAI_API_KEY fehlt in den Streamlit Secrets!")
    st.stop()

pay_link_90c = f"https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business={paypal_email}&item_name=ChefList_Pro_Rezept_Erstellung&amount=0.90&currency_code=EUR"

client = openai.OpenAI(api_key=api_key)

# --- 2. HILFSFUNKTIONEN ---
def get_full_video_data(video_url):
    try:
        ydl_opts = {
            'quiet': True, 
            'skip_download': True, 
            'writesubtitles': True, 
            'writeautomaticsub': True, 
            'subtitleslangs': ['de', 'en'],
            'no_warnings': True
        }
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
                if res.status_code == 200:
                    data = res.json()
                    transcript = " ".join([seg.get('utf8', '').strip() for event in data.get('events', []) if 'segs' in event for seg in event['segs'] if seg.get('utf8', '')])

        return video_title, transcript, description
    except Exception as e:
        return "Rezept", "", ""

def generate_smart_recipe(transcript, description, tag, portions, unit_system):
    # Fallback: Wenn kein Transkript da ist, nutzen wir nur die Beschreibung
    combined_input = f"TITEL: {transcript}\n\nBESCHREIBUNG: {description}"
    if not transcript and not description:
        return None
        
    unit_instruction = "METRISCH (g/ml)" if unit_system == "Metrisch (g/ml)" else "US-Einheiten (cups/oz)"
    
    system_prompt = f"""
    Du bist ein Profi-Koch. Erstelle ein Rezept für {portions} Person(en) im System {unit_instruction}.
    Nutze NUR dieses Link-Format: https://www.amazon.de/s?k=[ZUTATENNAME]&tag={tag}
    Inhalt: Dauer, Schwierigkeit, Backtemperatur, Mengen-Tabelle, Zubereitung.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input[:15000]}]
        )
        return response.choices[0].message.content
    except:
        return None

# --- 3. PDF GENERATOR ---
def create_pdf(text_content, recipe_title):
    pdf = FPDF()
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    
    display_title = recipe_title[:40] + "..." if len(recipe_title) > 40 else recipe_title
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font("Arial", style="B", size=14)
    
    try:
        safe_header = f"Rezept: {display_title}".encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(190, 15, txt=safe_header, ln=True, align='C', fill=True)
    except:
        pdf.cell(190, 15, txt="Dein Rezept", ln=True, align='C', fill=True)
    
    pdf.ln(5)
    
    is_instruction = False
    for line in text_content.split('\n'):
        line = line.strip()
        if not line or '---' in line: continue
        
        if 'Zubereitung' in line:
            is_instruction = True
            pdf.ln(5)
            pdf.set_font("Arial", style="B", size=12)
            pdf.cell(0, 10, txt="Zubereitung:", ln=True)
            continue
        
        if '|' in line and not is_instruction:
            pdf.set_font("Arial", size=11)
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 2:
                content = f"[  ] {parts[0]} {parts[1]}".replace('*', '')
                try:
                    pdf.cell(190, 8, txt=content.encode('latin-1', 'replace').decode('latin-1'), ln=True)
                except: continue
        else:
            pdf.set_font("Arial", size=10)
            clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line).replace('*', '')
            try:
                pdf.multi_cell(190, 7, txt=clean_text.encode('latin-1', 'replace').decode('latin-1'), align='L')
            except: continue

    pdf.ln(10)
    pdf.set_font("Arial", style="I", size=10)
    pdf.cell(0, 10, txt="Guten Appetit wuenscht das Team von ChefList Pro!", ln=True, align='C')
    return bytes(pdf.output())

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")

if "counter" not in st.session_state: st.session_state.counter = 0
if "recipe_result" not in st.session_state: st.session_state.recipe_result = None
if "recipe_title" not in st.session_state: st.session_state.recipe_title = ""

with st.sidebar:
    st.title("🍳 ChefList Pro")
    st.info(f"Rezepte erstellt: {st.session_state.counter}")
    st.markdown(f'''<a href="{pay_link_90c}" target="_blank"><button style="width: 100%; background-color: #0070ba; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold;">⚡ Rezept unterstützen (0,90€)</button></a>''', unsafe_allow_html=True)
    st.markdown("---")
    with st.expander("ℹ️ Info & Rechtliches"):
        st.caption(f"Betreiber: Markus Simmel\n\nKontakt: legemasim@gmail.com")
        st.caption("Affiliate: Als Amazon-Partner verdiene ich an Verkäufen.")

st.title("🍲 ChefList Pro")

video_url = st.text_input("YouTube Link:", placeholder="https://www.youtube.com/watch?v=...")
c1, c2 = st.columns(2)
portions = c1.slider("Portionen:", 1, 10, 4)
unit_system = c2.radio("Einheiten:", ["Metrisch (g/ml)", "US-Einheiten"], horizontal=True)

if st.button("Rezept jetzt erstellen ✨", use_container_width=True):
    if video_url:
        with st.status("Verarbeite Video...", expanded=True) as status:
            title, transcript, desc = get_full_video_data(video_url)
            st.session_state.recipe_title = title
            result = generate_smart_recipe(transcript, desc, amazon_tag, portions, unit_system)
            
            if result:
                st.session_state.recipe_result = result
                st.session_state.counter += 1
                status.update(label="Fertig!", state="complete", expanded=False)
            else:
                st.error("Leider konnten keine Rezept-Daten gefunden werden.")

if st.session_state.recipe_result:
    st.divider()
    st.subheader(st.session_state.recipe_title)
    st.markdown(st.session_state.recipe_result)
    
    pdf_bytes = create_pdf(st.session_state.recipe_result, st.session_state.recipe_title)
    st.download_button("📄 PDF herunterladen", pdf_bytes, file_name="Rezept.pdf", mime="application/pdf", use_container_width=True)
