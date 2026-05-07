import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

st.title("📦 Czytnik Etykiet Fresh World")
api_key = st.sidebar.text_input("Wklej tutaj swój Klucz API:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    pliki = st.file_uploader("Wybierz zdjęcia etykiet:", accept_multiple_files=True)

    if st.button("🚀 ODCZYTAJ DANE"):
        tabela_wynikow = []
        for p in pliki:
            with st.spinner(f"Analizuję: {p.name}"):
                obraz = Image.open(p)
                zadanie = "Wyciągnij: PRODUKT / RODZAJ / MARKA / KRAJ / KALIBER KL [KLASA]; NUMER DOSTAWY. Pisz WIELKIMI LITERAMI. Użyj średnika."
                try:
                    odpowiedz = model.generate_content([zadanie, obraz])
                    tekst = odpowiedz.text.replace('```csv', '').replace('```', '').strip()
                    dane = pd.read_csv(io.StringIO(tekst), sep=';', header=None)
                    tabela_wynikow.append(dane)
                except:
                    st.error(f"Błąd przy pliku {p.name}")
        
        if tabela_wynikow:
            finalna_tabela = pd.concat(tabela_wynikow)
            finalna_tabela.columns = ["NAZWA / KRAJ / KLASA", "NUMER DOSTAWY"]
            st.table(finalna_tabela)
else:
    st.info("👈 Wklej klucz API po lewej stronie.")