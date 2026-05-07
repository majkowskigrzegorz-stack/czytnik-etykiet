import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

st.set_page_config(page_title="Czytnik Fresh World", layout="wide")
st.title("📦 Czytnik Etykiet Fresh World")

api_key = st.sidebar.text_input("Wklej tutaj swój Klucz API:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # AUTOMATYCZNE SZUKANIE DOSTĘPNEGO MODELU
        # Sprawdzamy co Google ma aktualnie w ofercie
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Wybieramy najnowszego Flasha (szukamy czegokolwiek z 'flash')
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        
        st.sidebar.info(f"Połączono! Silnik: {wybrany_model}")
        model = genai.GenerativeModel(wybrany_model)
        
        pliki = st.file_uploader("Wybierz zdjęcia etykiet:", accept_multiple_files=True)

        if st.button("🚀 ODCZYTAJ DANE"):
            tabela_wynikow = []
            for p in pliki:
                with st.spinner(f"Analizuję: {p.name}"):
                    obraz = Image.open(p)
                    zadanie = "Wyciągnij dane: PRODUKT / RODZAJ / MARKA / KRAJ / KALIBER KL [KLASA]; NUMER DOSTAWY. Pisz WIELKIMI LITERAMI. Separator średnik."
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        if odpowiedz.text:
                            tekst = odpowiedz.text.replace('```csv', '').replace('```', '').strip()
                            # Czytamy tekst i zamieniamy na tabelkę
                            dane = pd.read_csv(io.StringIO(tekst), sep=';', header=None)
                            tabela_wynikow.append(dane)
                    except Exception as e:
                        st.error(f"Błąd przy pliku {p.name}: {e}")
            
            if tabela_wynikow:
                finalna_tabela = pd.concat(tabela_wynikow)
                finalna_tabela.columns = ["PRODUKT / KRAJ / KLASA", "NUMER DOSTAWY"]
                st.table(finalna_tabela)
                
    except Exception as e:
        st.error(f"Problem z połączeniem: {e}")
else:
    st.info("👈 Wklej klucz API po lewej stronie.")
