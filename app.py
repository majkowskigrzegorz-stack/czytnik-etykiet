import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import time

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
                with st.spinner(f"Analizuję etykiety z: {p.name}... Proszę o cierpliwość."):
                    obraz = Image.open(p)
                    zadanie = """
                    Odczytaj KAŻDĄ etykietę ze zdjęcia. Dla każdej etykiety wypisz:
                    PRODUKT / MARKA / KRAJ / KALIBER / KLASA (napisz KL i numer) | NUMER DOSTAWY
                    Użyj WIELKICH LITER.
                    """
                    
                    # PRÓBA ODCZYTU Z OBSŁUGĄ LIMITÓW (RETRIES)
                    max_prob = 3
                    for i in range(max_prob):
                        try:
                            odpowiedz = model.generate_content([zadanie, obraz])
                            if odpowiedz.text:
                                linie = odpowiedz.text.strip().split('\n')
                                for linia in linie:
                                    if "|" in linia:
                                        czesci = linia.split("|")
                                        wszystkie_wiersze.append([czesci[0].strip(), czesci[1].strip()])
                            break # Udało się, wychodzimy z pętli prób
                        except Exception as e:
                            if "429" in str(e) and i < max_prob - 1:
                                st.warning(f"Limit Google przekroczony. Czekam 30 sekund na odblokowanie (Próba {i+1}/{max_prob})...")
                                time.sleep(35) # Czekamy 35 sekund
                            else:
                                st.error(f"Nie udało się odczytać {p.name}: {e}")
                                break
            
            if wszystkie_wiersze:
                df = pd.DataFrame(wszystkie_wiersze, columns=["PRODUKT / MARKA / KRAJ / KLASA", "NUMER DOSTAWY"])
                st.success(f"Analiza zakończona! Odnaleziono {len(wszystkie_wiersze)} pozycji.")
                st.table(df)
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz tabelę do Excela", csv, "etykiety.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Problem z połączeniem: {e}")
else:
    st.info("👈 Wklej klucz API po lewej stronie.")
