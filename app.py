import streamlit as st
import openai
import requests
import re
import urllib.parse as urlparse

# --- KONFIGURATION ---
api_key = st.secrets["OPENAI_API_KEY"]
amazon_tag = "markusapp-21" 

if not api_key:
    st.error("Bitte trage deinen OpenAI API Key ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- FUNKTION: VIDEO ID EXTRAHIEREN ---
def extract_video_id(url):
    if "v=" in url:
        return url.split("v=")[1][:11]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1][:11]
    elif "shorts/" in url:
        return url.split("shorts/")[1][:11]
    else:
        return None

# --- DER PIRATEN-HACK: UNTERTITEL ÜBER PROXY HOLEN ---
def get_transcript(video_url):
    """Zieht den Text nicht von YouTube, sondern über geheime Piped-Proxys"""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("❌ Link-Format nicht erkannt.")
            return None

        # Wir fragen 3 verschiedene Server an. Wenn einer blockiert ist, springen wir zum nächsten.
        instances = [
            "https://pipedapi.kavin.rocks",
            "https://pipedapi.leptons.xyz",
            "https://pipedapi.lunar.icu"
        ]
        
        data = None
        for instance in instances:
            try:
                # Wir fragen den geheimen Server nach dem Video
                res = requests.get(f"{instance}/streams/{video_id}", timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    break # Erfolg! Schleife abbrechen
            except:
                continue # Wenn Server tot, probiere den nächsten
                
        if not data or "subtitles" not in data or not data["subtitles"]:
            st.error("❌ Keine Untertitel im Proxy-Netzwerk gefunden.")
            return None
            
        # Wir suchen deutsche Untertitel. Wenn nicht da, englisch. Sonst den allerersten.
        subtitles = data["subtitles"]
        target_sub = next((s for s in subtitles if s.get("code") in ["de", "en"]), subtitles[0])
        
        # Untertitel-Text herunterladen
        raw_text = requests.get(target_sub["url"]).text
        
        # Text radikal bereinigen (egal ob XML oder VTT Format)
        clean_text = re.sub(r'<[^>]+>', ' ', raw_text) # Alle HTML/XML Tags löschen
        clean_text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}', ' ', clean_text) # Zeitstempel löschen
        clean_text = clean_text.replace('WEBVTT', '').replace('Kind: captions', '')
        clean_text = " ".join(clean_text.split()) # Leerzeichen glätten
        
        return clean_text

    except Exception as e:
        st.error(f"❌ Fehler beim Abrufen der Untertitel: {str(e)}")
        return None

# --- KI FUNKTION ---
def generate_smart_list(text, tag):
    system_prompt = f"""
    Du bist ein hilfreicher Koch-Assistent.
    
    DEINE AUFGABE:
    1. Analysiere das Transkript und extrahiere alle Zutaten.
    2. Suche explizit nach MENGENANGABEN.
    3. Erstelle eine Markdown-Tabelle mit 3 Spalten: "Menge", "Zutat", "Kaufen".
    
    WICHTIG - DER LINK:
    Das Format für den Link in der Spalte "Kaufen" ist: https://www.amazon.de/s?k=[ZUTAT]&tag={tag}
    Ersetze [ZUTAT] durch den exakten Namen. Der Link-Text ist "🛒 Auf Amazon suchen".
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"KI-Fehler: {str(e)}")
        return None

# --- INTERFACE ---
st.set_page_config(page_title="ChefList Pro", page_icon="🍲")

st.title("🍲 ChefList Pro (Turbo Version ⚡)")
st.write("Füge einen YouTube-Link ein. Ich lese das Rezept in 2 Sekunden und erstelle die Einkaufsliste!")

video_url = st.text_input("YouTube Link:", placeholder="https://youtube.com/...")

if st.button("Liste generieren 💸"):
    if not video_url:
        st.warning("Bitte erst einen Link eingeben!")
    else:
        with st.status("Analysiere Rezept...", expanded=True) as status:
            
            st.write("1. Lese Untertitel über Proxy-Server... 🕵️‍♂️")
            text = get_transcript(video_url)
            
            if text:
                st.write("2. KI schreibt Einkaufsliste... 🧠")
                result = generate_smart_list(text, amazon_tag)
                
                status.update(label="Fertig!", state="complete", expanded=False)
                
                st.success("Hier ist deine smarte Liste:")
                st.markdown("---")
                st.markdown(result)


