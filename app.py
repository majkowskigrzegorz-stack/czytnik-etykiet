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
                with st.spinner(f"Analizuję: {p.name}"):
                    obraz = Image.open(p)
                    # Precyzyjna instrukcja dla AI
                    zadanie = "Odczytaj z etykiety: 1. PRODUKT/MARKA/KRAJ/KALIBER/KLASA, 2. NUMER DOSTAWY. Odpowiedz krótko: Dane1 | Dane2"
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        wynik = odpowiedz.text.strip()
                        
                        # Dzielimy wynik na kolumny bezpiecznym sposobem
                        if "|" in wynik:
                            czesci = wynik.split("|")
                            wszystkie_wiersze.append([czesci[0].strip(), czesci[1].strip()])
                        else:
                            wszystkie_wiersze.append([wynik, "Nie odnaleziono"])
                            
                    except Exception as e:
                        st.error(f"Błąd pliku {p.name}: {e}")
            
            if wszystkie_wiersze:
                df = pd.DataFrame(wszystkie_wiersze, columns=["PRODUKT / KRAJ / KLASA", "NUMER DOSTAWY"])
                st.success("Analiza zakończona!")
                st.table(df)
                
    except Exception as e:
        st.error(f"Problem: {e}")
else:
    st.info("👈 Wklej klucz API po lewej stronie.")
