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
        # Wymuszamy model 1.5 Flash - ma lepsze limity dla darmowych kont
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        pliki = st.file_uploader("Wybierz zdjęcia etykiet:", accept_multiple_files=True)

        if st.button("🚀 ODCZYTAJ DANE"):
            wszystkie_wiersze = []
            for p in pliki:
                with st.spinner(f"Analizuję: {p.name}..."):
                    obraz = Image.open(p)
                    # Skracamy instrukcję, by zużywać mniej "mocy"
                    zadanie = "Wypisz każdą etykietę ze zdjęcia w formacie: PRODUKT/MARKA/KRAJ/KALIBER/KLASA | NUMER DOSTAWY"
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        if odpowiedz.text:
                            linie = odpowiedz.text.strip().split('\n')
                            for linia in linie:
                                if "|" in linia:
                                    czesci = linia.split("|")
                                    wszystkie_wiersze.append([czesci[0].strip(), czesci[1].strip()])
                    except Exception as e:
                        if "429" in str(e):
                            st.error("Google mówi: STOP. Wykorzystałeś darmowy limit na tę godzinę. Spróbuj ponownie za jakiś czas.")
                            break
                        else:
                            st.error(f"Błąd: {e}")
            
            if wszystkie_wiersze:
                df = pd.DataFrame(wszystkie_wiersze, columns=["DANE PRODUKTU", "NUMER DOSTAWY"])
                st.table(df)
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz Excel", csv, "etykiety.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Problem: {e}")
else:
    st.info("👈 Wklej klucz API po lewej stronie.")
