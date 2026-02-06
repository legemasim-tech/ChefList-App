import streamlit as st
import yt_dlp
import openai
import os
import time

# --- KONFIGURATION ---

# Wir holen den Key aus dem sicheren Tresor des Servers
api_key = st.secrets["OPENAI_API_KEY"]

# Das ist deine fiktive Amazon-Partner-ID. 
# Später würdest du hier deine echte ID eintragen (z.B. 'markusapp-21')
amazon_tag = "markusapp-21" 

# Sicherheitshalber prüfen
if not api_key or "HIER" in api_key:
    st.error("Bitte trage deinen OpenAI API Key im Code ein!")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- FUNKTIONEN ---

def download_audio(video_url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'temp_audio.%(ext)s',
        'quiet': True,
        'no_warnings': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return "temp_audio.mp3"
    except Exception as e:
        st.error(f"Download-Fehler: {str(e)}")
        return None

def transcribe_audio(file_path):
    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        return transcript.text
    except Exception as e:
        st.error(f"Transkriptions-Fehler: {str(e)}")
        return None

def generate_smart_list(text, tag):
    # Hier passiert die Magie: Wir erklären der KI genau, wie der Link aussehen muss.
    system_prompt = f"""
    Du bist ein hilfreicher Koch-Assistent.
    
    DEINE AUFGABE:
    1. Analysiere das Transkript und extrahiere alle Zutaten.
    2. Suche explizit nach MENGENANGABEN (Gramm, EL, TL, Stück). Wenn keine genannt wird, schätze basierend auf dem Kontext oder schreibe "nach Geschmack".
    3. Erstelle eine Markdown-Tabelle mit 3 Spalten: "Menge", "Zutat", "Kaufen".
    
    WICHTIG - DER LINK:
    In der Spalte "Kaufen" erstellst du einen Link für die Zutat.
    Das Format für den Link ist: https://www.amazon.de/s?k=[ZUTAT]&tag={tag}
    Ersetze [ZUTAT] durch den Namen der Zutat.
    Der Link-Text soll "🛒 Auf Amazon suchen" heißen.
    
    Beispiel für eine Zeile in der Tabelle:
    | 500g | Spaghetti | [🛒 Auf Amazon suchen](https://www.amazon.de/s?k=Spaghetti&tag={tag}) |
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

# --- DAS INTERFACE ---

st.set_page_config(page_title="ChefList Pro", page_icon="🍲")

st.title("🍲 ChefList Pro (Mit Einkaufs-Links)")
st.write("Füge einen YouTube-Link ein. Ich erstelle dir eine Einkaufsliste mit Mengen und Bestell-Links.")

video_url = st.text_input("YouTube Link:", placeholder="https://youtube.com/...")

if st.button("Liste generieren 💸"):
    if not video_url:
        st.warning("Bitte erst einen Link eingeben!")
    else:
        with st.status("Analysiere Rezept...", expanded=True) as status:
            
            st.write("1. Video laden... ⏳")
            audio_path = download_audio(video_url)
            
            if audio_path:
                st.write("2. Verstehe Sprache... 👂")
                text = transcribe_audio(audio_path)
                
                if text:
                    st.write("3. Erstelle Tabelle mit Links... 📊")
                    # Wir übergeben hier deine Amazon-ID an die Funktion
                    result = generate_smart_list(text, amazon_tag)
                    
                    status.update(label="Fertig!", state="complete", expanded=False)
                    
                    st.success("Hier ist deine smarte Liste:")
                    st.markdown("---")
                    # Das hier zeigt die Tabelle und macht die Links klickbar
                    st.markdown(result)
                    
                    # Aufräumen
                    time.sleep(1)
                    try:
                        os.remove(audio_path)
                    except:
                        pass