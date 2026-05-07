import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import time

# Konfiguracja profesjonalnego interfejsu
st.set_page_config(page_title="System Analizy Etykiet", layout="wide")
st.title("📦 System Automatycznego Odczytu Etykiet")

# Panel boczny
with st.sidebar:
    st.header("Konfiguracja")
    api_key = st.text_input("Klucz API Google:", type="password")
    st.info("System obsługuje formaty JPG, PNG i JPEG.")

def analyze_image(model, image):
    """Funkcja z wbudowanym mechanizmem ponawiania prób w przypadku limitów (Error 429)."""
    prompt = "Odczytaj wszystkie etykiety. Format: PRODUKT / MARKA / KRAJ / KALIBER / KLASA | NUMER DOSTAWY. Użyj WIELKICH LITER."
    
    for attempt in range(3):  # Maksymalnie 3 próby
        try:
            response = model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            if "429" in str(e):
                st.warning(f"Osiągnięto limit Google. Oczekiwanie 30 sekund na odblokowanie... (Próba {attempt + 1}/3)")
                time.sleep(30)
                continue
            raise e
    return None

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Dynamiczne wybieranie dostępnego modelu
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available_models if "flash" in m), available_models[0])
        model = genai.GenerativeModel(model_name)
        
        uploaded_files = st.file_uploader("Wgraj zdjęcia arkuszy z etykietami:", accept_multiple_files=True)

        if st.button("🚀 ROZPOCZNIJ PROCES ANALIZY"):
            results = []
            progress_bar = st.progress(0)
            
            for index, file in enumerate(uploaded_files):
                img = Image.open(file)
                raw_text = analyze_image(model, img)
                
                if raw_text:
                    for line in raw_text.strip().split('\n'):
                        if "|" in line:
                            parts = line.split("|")
                            results.append({"Dane Produktu": parts[0].strip(), "Nr Dostawy": parts[1].strip()})
                
                progress_bar.progress((index + 1) / len(uploaded_files))

            if results:
                st.subheader("Wyniki analizy")
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
                
                # Eksport do Excela
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz dane jako plik .CSV (do Excela)", csv, "raport.csv", "text/csv")
            else:
                st.error("Nie udało się odczytać żadnych danych. Sprawdź jakość zdjęć.")
                
    except Exception as e:
        st.error(f"Wystąpił błąd krytyczny: {e}")
else:
    st.warning("Proszę podać Klucz API w panelu bocznym, aby uruchomić system.")
