import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd

st.set_page_config(page_title="Czytnik Fresh World", layout="wide")
st.title("📦 Czytnik Etykiet Fresh World")

api_key = st.sidebar.text_input("Wklej tutaj swój Klucz API:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)
        
        pliki = st.file_uploader("Wybierz zdjęcia etykiet:", accept_multiple_files=True)

        if st.button("🚀 ODCZYTAJ DANE"):
            wszystkie_wiersze = []
            for p in pliki:
                with st.spinner(f"Analizuję wszystkie etykiety na zdjęciu: {p.name}"):
                    obraz = Image.open(p)
                    # NOWA, MOCNIEJSZA INSTRUKCJA
                    zadanie = """
                    Na tym zdjęciu znajduje się wiele etykiet. Odczytaj KAŻDĄ z nich po kolei.
                    Dla każdej etykiety przygotuj dwa pola oddzielone pionową kreską (|):
                    Pole 1: PRODUKT / MARKA / KRAJ / KALIBER / KLASA (na końcu dodaj 'KL' i numer klasy, np. KL1).
                    Pole 2: NUMER DOSTAWY (szukaj formatu P:XXXXX/XX lub I:XXXXX).
                    
                    Wypisz wszystkie odnalezione etykiety, każdą w nowej linii. 
                    Pisz WIELKIMI LITERAMI.
                    Przykład formatu:
                    MANGO / FRESHGO / BRAZYLIA / 8 / KL1 | P:16058/26
                    LIMONKI / FRESHGO / BRAZYLIA / 48-57 MM / KL1 | P:15022/26
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        linie = odpowiedz.text.strip().split('\n')
                        
                        for linia in linie:
                            if "|" in linia:
                                czesci = linia.split("|")
                                wszystkie_wiersze.append([czesci[0].strip(), czesci[1].strip()])
                    except Exception as e:
                        st.error(f"Błąd przy pliku {p.name}: {e}")
            
            if wszystkie_wiersze:
                df = pd.DataFrame(wszystkie_wiersze, columns=["PRODUKT / MARKA / KRAJ / KALIBER / KLASA", "NUMER DOSTAWY"])
                st.success(f"Analiza zakończona! Odnaleziono {len(wszystkie_wiersze)} pozycji.")
                st.table(df)
                
                # Dodatkowo dodajemy przycisk do pobrania Excela (CSV)
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz tabelę do Excela", csv, "etykiety.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Problem: {e}")
else:
    st.info("👈 Wklej klucz API po lewej stronie.")
