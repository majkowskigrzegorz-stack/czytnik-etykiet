import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json

st.set_page_config(page_title="Fresh World - Data Entry", layout="wide")
st.title("📊 Ekstraktor Danych pod Formułę Excel")

api_key = st.sidebar.text_input("Klucz API:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Automatyczny wybór najnowszego dostępnego modelu
        model_name = "gemini-2.5-flash" # Model z Twojego screena, który działał
        model = genai.GenerativeModel(model_name)

        pliki = st.file_uploader("Wgraj zdjęcia etykiet:", accept_multiple_files=True)

        if st.button("🚀 PRZYGOTUJ DANE DO WKLEJENIA"):
            wszystkie_wyniki = []
            
            for p in pliki:
                with st.spinner(f"Przetwarzanie: {p.name}..."):
                    obraz = Image.open(p)
                    
                    # Prompt zsynchronizowany z Twoją formułą Excel
                    zadanie = """
                    Odczytaj dane z etykiet i zwróć wyłącznie LISTĘ JSON.
                    Dopasuj dane ściśle do tych kluczy (odpowiadają kolumnom w Twoim Excelu):
                    
                    "E": Produkt
                    "F": Kolor miąższu (jeśli jest, np. żółty)
                    "G": Odmiana
                    "H": Masa netto (sama wartość, np. 3kg)
                    "I": Pochodzenie (Kraj)
                    "J": Klasa (np. 1 lub I)
                    "K": Liczba sztuk (np. 16X6)
                    "L": Wielkość (np. 48-57MM)
                    "M": Identyfikacja produktu (Numer dostawy P/I)
                    "N": NRDD (Numer NRDD)
                    
                    ZASADY:
                    1. Pomiń słowo FRESHWORLD.
                    2. Jeśli danej wartości nie ma na zdjęciu, wpisz "".
                    3. Zwróć czysty kod JSON, bez żadnych dodatkowych komentarzy.
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        clean_json = odpowiedz.text.replace('```json', '').replace('```', '').strip()
                        dane = json.loads(clean_json)
                        wszystkie_wyniki.extend(dane)
                    except Exception as e:
                        st.error(f"Błąd przy pliku {p.name}: {e}")

            if wszystkie_wyniki:
                df = pd.DataFrame(wszystkie_wyniki)
                # Sztywne ustawienie kolumn, aby pasowały do Twojego arkusza E-N
                kolumny_cel = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]
                df = df.reindex(columns=kolumny_cel)
                
                # Czytelne nagłówki dla podglądu
                df.columns = ["Produkt (E)", "Kolor (F)", "Odmiana (G)", "Masa (H)", "Kraj (I)", "Klasa (J)", "Sztuki (K)", "Wielkość (L)", "ID (M)", "NRDD (N)"]
                
                st.subheader("Gotowe dane (Skopiuj i wklej do Excela od kolumny E):")
                st.dataframe(df, use_container_width=True)
                
                # Eksport do CSV (separator średnik dla polskiego Excela)
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz plik .csv", csv, "dane_do_excela.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Błąd systemu: {e}")
else:
    st.warning("Wpisz Klucz API, aby kontynuować.")
