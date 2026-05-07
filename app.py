import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd

st.set_page_config(page_title="Czytnik Fresh World PRO", layout="wide")
st.title("📦 System Ewidencji Dostaw Fresh World")

with st.sidebar:
    st.header("Ustawienia")
    api_key = st.sidebar.text_input("Wklej Klucz API:", type="password")
    st.info("Zalecany model dla wersji płatnej: **Gemini 2.5 Flash**")

if api_key:
    try:
        genai.configure(api_key=api_key)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia arkuszy/etykiet:", accept_multiple_files=True)

        if st.button("🚀 GENERUJ TABELĘ DOSTAW"):
            wszystkie_dane = []
            for p in pliki:
                with st.spinner(f"Analizuję: {p.name}..."):
                    obraz = Image.open(p)
                    
                    # POPRAWIONE POLECENIE - BLOKADA SŁOWA FRESHWORLD
                    zadanie = """
                    Zanalizuj zdjęcie i stwórz tabelę z dwiema kolumnami oddzielonymi znakiem (|).
                    Wypisz każdą etykietę/pozycję ze zdjęcia.
                    
                    ZASADA KRYTYCZNA: Pod żadnym pozorem NIE DOPISUJ słowa 'FRESHWORLD' ani 'FRESH WORLD' do żadnej z kolumn. Pomiń tę nazwę całkowicie.
                    
                    KOLUMNA 1 (PRODUKT / RODZAJ / MARKA / KRAJ / KALIBER): 
                    Wypisz nazwę towaru, odmianę, markę, kraj pochodzenia i kaliber. 
                    Pamiętaj: Usuń słowo 'FRESHWORLD' z opisu.
                    
                    KOLUMNA 2 (NUMER DOSTAWY (IDENTYFIKACJA PRODUKTU)): 
                    Wypisz TYLKO numer dostawy (np. P:20285/26 lub I:XXXXX).
                    
                    Format: DaneProduktu | NumerDostawy
                    Pisz wszystko WIELKIMI LITERAMI.
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
                df = pd.DataFrame(wszystkie_dane)
                st.table(df)
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz tabelę", csv, "dostawy.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Błąd konfiguracji: {e}")
else:
    st.warning("Wklej Klucz API po lewej stronie.")
