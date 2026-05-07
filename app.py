import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd

st.set_page_config(page_title="Czytnik Fresh World PRO", layout="wide")
st.title("📦 System Ewidencji Dostaw")

with st.sidebar:
    st.header("Ustawienia")
    api_key = st.text_input("Wklej Klucz API:", type="password")
    st.info("Zalecany model: **Gemini 2.5 Flash** (wersja płatna)")

if api_key:
    try:
        genai.configure(api_key=api_key)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia:", accept_multiple_files=True)

        if st.button("🚀 GENERUJ CZYSTĄ TABELĘ"):
            wszystkie_dane = []
            for p in pliki:
                with st.spinner(f"Analizuję: {p.name}..."):
                    obraz = Image.open(p)
                    
                    # MAKSYMALNIE PRECYZYJNY PROMPT
                    zadanie = """
                    WYMÓG BEZWZGLĘDNY: 
                    1. NIE używaj słów: 'PRODUKT:', 'ODMIANA:', 'POCHODZENIE:', 'LICZBA SZTUK:', 'MARKA:'.
                    2. NIE używaj słowa 'FRESHWORLD' ani 'FRESH WORLD'.
                    3. Wypisz TYLKO czyste dane odczytane z etykiet.
                    
                    Format każdej linii:
                    NAZWA_TOWARU ODMIANA KRAJ_POCHODZENIA KALIBER_LUB_WAGA | NUMER_DOSTAWY
                    
                    Przykład poprawnej linii:
                    MANGO PALMER BRAZYLIA 8X2SZT | P:15058/26
                    
                    Zasady:
                    - Separator to pionowa kreska (|).
                    - Wszystko WIELKIMI LITERAMI.
                    - Każda etykieta to osobny wiersz.
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        linie = odpowiedz.text.strip().split('\n')
                        for linia in linie:
                            if "|" in linia:
                                czesci = linia.split("|")
                                wszystkie_dane.append({
                                    "PRODUKT / RODZAJ / MARKA / KRAJ / KALIBER": czesci[0].strip(),
                                    "NUMER DOSTAWY (IDENTYFIKACJA PRODUKTU)": czesci[1].strip()
                                })
                    except Exception as e:
                        st.error(f"Błąd: {e}")

            if wszystkie_dane:
                df = pd.DataFrame(wszystkie_dane)
                # Wyświetlamy jako czystą tabelę
                st.table(df)
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz Excel (CSV)", csv, "dostawy_clean.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Błąd konfiguracji: {e}")
else:
    st.warning("Proszę podać Klucz API.")
