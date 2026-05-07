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
        
        # AUTOMATYCZNE SZUKANIE MODELU (Naprawia błąd 404)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        
        st.sidebar.success(f"Połączono! Silnik: {wybrany_model}")
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia etykiet", accept_multiple_files=True)

        if st.button("🚀 ODCZYTAJ WSZYSTKIE DANE"):
            tabela_danych = []
            for p in pliki:
                with st.spinner(f"Przetwarzam: {p.name}..."):
                    obraz = Image.open(p)
                    # Instrukcja wymuszająca Twój format
                    zadanie = """
                    Odczytaj KAŻDĄ etykietę na zdjęciu. Dla każdej stwórz jeden wiersz:
                    PRODUKT / MARKA / KRAJ / KALIBER / KLASA (napisz KL i numer) | NUMER DOSTAWY
                    Użyj znaku | jako rozdzielacza. Pisz WIELKIMI LITERAMI.
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        linie = odpowiedz.text.strip().split('\n')
                        for linia in linie:
                            if "|" in linia:
                                czesci = linia.split("|")
                                tabela_danych.append([czesci[0].strip(), czesci[1].strip()])
                    except Exception as e:
                        st.error(f"Błąd przy pliku {p.name}: {e}")
            
            if tabela_danych:
                df = pd.DataFrame(tabela_danych, columns=["PRODUKT / MARKA / KRAJ / KLASA", "NUMER DOSTAWY"])
                st.success("Gotowe!")
                st.table(df)
                
                # Przycisk do pobrania Excela
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz do Excela", csv, "raport_etykiet.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Błąd konfiguracji: {e}")
else:
    st.info("👈 Wklej klucz API w polu po lewej stronie.")
