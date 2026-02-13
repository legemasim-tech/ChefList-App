import streamlit as st
import openai
from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse as urlparse

# --- KONFIGURATION ---
api_key = st.secrets["OPENAI_API_KEY"]
amazon_tag = "markusapp-21" 

if not api_key:
    st.error("Bitte trage deinen OpenAI API Key ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- NEUE FUNKTION: UNTERTITEL KLAUEN (ROBUST) ---
def extract_video_id(url):
    """Holt die Video-ID aus allen möglichen YouTube-Links (auch Shorts oder youtu.be)"""
    if "v=" in url:
        return url.split("v=")[1][:11]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1][:11]
    elif "shorts/" in url:
        return url.split("shorts/")[1][:11]
    else:
        return None

def get_transcript(video_url):
    """Zieht heimlich den Text aus YouTube (funktioniert in jeder Paket-Version!)"""
    try:
        video_id = extract_video_id(video_url)
        if not video_id:
            st.error("❌ Link-Format nicht erkannt. Bitte einen normalen YouTube-Link nutzen.")
            return None

        # Wir geben eine breite Liste an Sprachen mit. Er nimmt den ersten Treffer!
        # Auch automatisch generierte Untertitel dieser Sprachen werden akzeptiert.
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, 
            languages=['de', 'en', 'en-US', 'en-GB', 'es', 'fr', 'it', 'tr', 'ru', 'pt']
        )
        
        text = " ".join([t['text'] for t in transcript_list])
        return text
            
    except Exception as e:
        st.error(f"❌ YouTube hat hier keine Untertitel (oder der Creator hat sie gesperrt): {str(e)}")
        return None

# --- KI FUNKTION (Bleibt gleich) ---
def generate_smart_list(text, tag):
    system_prompt = f"""
    Du bist ein hilfreicher Koch-Assistent.
    
    DEINE AUFGABE:
    1. Analysiere das Transkript und extrahiere alle Zutaten.
    2. Suche explizit nach MENGENANGABEN.
    3. Erstelle eine Markdown-Tabelle mit 3 Spalten: "Menge", "Zutat", "Kaufen".
    
    WICHTIG - DER LINK:
    Das Format für den Link in der Spalte "Kaufen" ist: https://www.amazon.de/s?k=[ZUTAT]&tag={tag}
    Ersetze [ZUTAT] durch den Namen. Der Link-Text ist "🛒 Auf Amazon suchen".
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
            
            st.write("1. Lese Untertitel aus YouTube... 🕵️‍♂️")
            text = get_transcript(video_url)
            
            if text:
                st.write("2. KI schreibt Einkaufsliste... 🧠")
                result = generate_smart_list(text, amazon_tag)
                
                status.update(label="Fertig!", state="complete", expanded=False)
                
                st.success("Hier ist deine smarte Liste:")
                st.markdown("---")
                st.markdown(result)


