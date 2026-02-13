import streamlit as st
import openai
import requests
import re
import urllib.parse as urlparse
# Die Profi-Bibliothek und das NEUE Proxy-Modul
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

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
                
# --- DIE PROFI-LÖSUNG: UNTERTITEL ÜBER PROXY-SERVER HOLEN ---
def get_transcript(video_url):
    """Holt Untertitel über die YouTube-API (Neue Syntax V1.0+ mit Proxy)"""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("❌ Link-Format nicht erkannt.")
            return None

        # Hier wieder DEINE Webshare-Daten eintragen!
        proxy_url = "http://dgashpyp:izspbf3gjypg@31.59.20.176:6754"
        
        proxy_config = GenericProxyConfig(
            http_url=proxy_url,
            https_url=proxy_url
        )

        # 1. Wir initialisieren die API direkt "getarnt" mit dem Proxy
        api = YouTubeTranscriptApi(proxy_config=proxy_config)
        
        # 2. Wir rufen die Liste der Untertitel ab
        transcript_list = api.list(video_id)
        
        # 3. Wir suchen gezielt nach Deutsch oder Englisch
        transcript = transcript_list.find_transcript(['de', 'en'])
        
        # 4. Wir laden den Text herunter (Das ist jetzt ein Objekt!)
        transcript_data = transcript.fetch()
        
        # 5. DER FIX: Wir nutzen fragment.text (mit Punkt) statt eckiger Klammern!
        clean_text = " ".join([fragment.text for fragment in transcript_data])
        
        # 6. Text bereinigen
        clean_text = " ".join(clean_text.split())
        
        return clean_text

    except Exception as e:
        st.error(f"❌ Keine Untertitel gefunden. Info: {str(e)}")
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












