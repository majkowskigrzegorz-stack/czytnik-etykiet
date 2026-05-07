import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json

# Konfiguracja strony
st.set_page_config(page_title="Fresh World - System Czystych Danych", layout="wide")
st.title("📦 Generator Składników do Arkusza")

api_key = st.sidebar.text_input("Klucz API:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia etykiet:", accept_multiple_files=True)

        if st.button("🚀 WYGENERUJ DANE DO EXCELA"):
            wszystkie_wyniki = []
            
            for p in pliki:
                with st.spinner(f"Przetwarzanie {p.name}..."):
                    obraz = Image.open(p)
                    # Prompt wymuszający czyste dane bez żadnych dopisków
                    zadanie = """
                    Odczytaj dane i zwróć TYLKO czystą listę JSON.
                    Dopasuj dane do tych kluczy (odpowiadają Twoim kolumnom w Excelu):
                    "Produkt": (kolumna E)
                    "Kolor_Miaszu": (kolumna F - np. ŻÓŁTY, jeśli jest)
                    "Odmiana": (kolumna G)
                    "Masa_Netto": (kolumna H - sama wartość, np. 3KG)
                    "Pochodzenie": (kolumna I)
                    "Klasa": (kolumna J - sama cyfra lub rzymska)
                    "Liczba_Sztuk": (kolumna K - np. 16X6)
                    "Wielkosc": (kolumna L - np. 48-57MM)
                    "Identyfikacja": (kolumna M - Numer dostawy P/I)
                    "NRDD": (kolumna N - Numer NRDD)
                    
                    ZASADY:
                    1. ZERO słowa FRESHWORLD.
                    2. Jeśli czegoś nie ma, wpisz "".
                    3. NIE twórz kolumny Opis (Excel zrobi ją sam Twoją formułą).
                    4. Zwróć wyłącznie czysty JSON.
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        clean_json = odpowiedz.text.replace('```json', '').replace('```', '').strip()
                        dane = json.loads(clean_json)
                        wszystkie_wyniki.extend(dane)
                    except Exception as e:
                        st.error(f"Błąd w pliku {p.name}: {e}")

            if wszystkie_wyniki:
                df = pd.DataFrame(wszystkie_wyniki)
                # Ustawienie kolejności kolumn pod Twój Excel
                kolumny_excel = ["Produkt", "Kolor_Miaszu", "Odmiana", "Masa_Netto", "Pochodzenie", "Klasa", "Liczba_Sztuk", "Wielkosc", "Identyfikacja", "NRDD"]
                df = df.reindex(columns=kolumny_excel)
                
                st.subheader("Czyste dane do wklejenia:")
                st.dataframe(df)
                
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz plik do Excela", csv, "dane_do_arkusza.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Błąd konfiguracji: {e}")
else:
    st.info("Wklej Klucz API w panelu bocznym.")
