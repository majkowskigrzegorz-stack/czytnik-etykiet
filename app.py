import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

st.set_page_config(page_title="Czytnik Fresh World PRO", layout="wide")
st.title("📦 System Ewidencji Dostaw Fresh World")

# Sidebar dla konfiguracji
with st.sidebar:
    st.header("Ustawienia")
    api_key = st.text_input("Wklej Klucz API:", type="password")
    st.write("---")
    st.info("Zalecany model dla wersji płatnej: **Gemini 2.5 Flash**")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Automatyczny dobór najlepszego modelu (np. Gemini 2.5 Flash lub nowszy)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia arkuszy/etykiet:", accept_multiple_files=True)

        if st.button("🚀 GENERUJ TABELĘ DOSTAW"):
            wszystkie_dane = []
            
            for p in pliki:
                with st.spinner(f"Analizuję plik: {p.name}..."):
                    obraz = Image.open(p)
                    
                    # TWOJE PRECYZYJNE POLECENIE
                    zadanie = """
                    Zanalizuj zdjęcie i stwórz tabelę z dwiema kolumnami oddzielonymi znakiem (|).
                    Wypisz każdą etykietę/pozycję ze zdjęcia.
                    
                    KOLUMNA 1 (PRODUKT / RODZAJ / MARKA / KRAJ / KALIBER): 
                    Wypisz nazwę towaru, odmianę, markę, kraj pochodzenia i kaliber (jeśli jest).
                    
                    KOLUMNA 2 (NUMER DOSTAWY (IDENTYFIKACJA PRODUKTU)): 
                    Wypisz numer dostawy (np. P:20285/26 lub I:XXXXX).
                    
                    Zasady:
                    - Pisz wszystko WIELKIMI LITERAMI.
                    - Każda etykieta to nowa linia.
                    - Format: DaneProduktu | NumerDostawy
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
                        st.error(f"Błąd w pliku {p.name}: {e}")

            if wszystkie_dane:
                st.subheader("📋 Wynikowa Tabela Dostaw")
                df = pd.DataFrame(wszystkie_dane)
                
                # Wyświetlanie tabeli w formacie, który chciałeś
                st.dataframe(df, use_container_width=True)
                
                # Przycisk pobierania
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz tabelę (CSV do Excela)", csv, "dostawy.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Błąd konfiguracji systemu: {e}")
else:
    st.warning("Aby rozpocząć, wklej swój Klucz API w panelu bocznym.")
