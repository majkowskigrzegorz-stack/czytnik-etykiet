import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io
import time

st.set_page_config(page_title="Czytnik Fresh World", layout="wide")
st.title("📦 Czytnik Etykiet Fresh World")

api_key = st.sidebar.text_input("Wklej tutaj swój Klucz API:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        pliki = st.file_uploader("Wybierz zdjęcia etykiet:", accept_multiple_files=True)

        if st.button("🚀 ODCZYTAJ DANE"):
            tabela_wynikow = []
            for p in pliki:
                with st.spinner(f"Analizuję: {p.name}"):
                    obraz = Image.open(p)
                    zadanie = "Wyciągnij dane z etykiety. Interesuje mnie: PRODUKT / RODZAJ / MARKA / KRAJ / KALIBER oraz KLASA (zapisz jako KL i numer). Drugi element to NUMER DOSTAWY. Zwróć dane jako tekst oddzielony średnikami (;). Pisz tylko WIELKIMI LITERAMI."
                    
                    try:
                        # Dodajemy krótką pauzę, żeby nie przeciążyć klucza
                        time.sleep(1) 
                        odpowiedz = model.generate_content([zadanie, obraz])
                        
                        if odpowiedz.text:
                            tekst = odpowiedz.text.replace('```csv', '').replace('```', '').strip()
                            dane = pd.read_csv(io.StringIO(tekst), sep=';', header=None)
                            tabela_wynikow.append(dane)
                    except Exception as e:
                        st.error(f"Szczegóły błędu dla {p.name}: {e}")
            
            if tabela_wynikow:
                finalna_tabela = pd.concat(tabela_wynikow)
                finalna_tabela.columns = ["PRODUKT / KRAJ / MARKA / KLASA", "NUMER DOSTAWY"]
                st.success("Analiza zakończona!")
                st.table(finalna_tabela)
    except Exception as e:
        st.error(f"Problem z kluczem API: {e}")
else:
    st.info("👈 Wklej klucz API po lewej stronie, aby zacząć.")
