import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json

st.set_page_config(page_title="Fresh World PRO - Stabilny System", layout="wide")
st.title("📊 Profesjonalny Czytnik Etykiet (Wersja Stabilna)")

api_key = st.sidebar.text_input("Klucz API:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia:", accept_multiple_files=True)

        if st.button("🚀 GENERUJ TABELĘ"):
            wszystkie_dane = []
            for p in pliki:
                with st.spinner(f"Analizuję {p.name}..."):
                    obraz = Image.open(p)
                    # Wymuszamy JSON - to zapobiega przesuwaniu kolumn widocznym na Twoim foto
                    zadanie = """
                    Odczytaj etykiety i zwróć dane wyłącznie jako LISTA JSON. 
                    Każdy produkt to obiekt z kluczami:
                    "Produkt", "Odmiana", "Masa netto", "Pochodzenie", "Klasa", "Liczba sztuk", "Wielkość", "Identyfikacja", "NRDD", "Status", "Opis"
                    
                    ZASADY:
                    1. Nigdy nie używaj słowa FRESHWORLD.
                    2. Jeśli danej cechy nie ma na zdjęciu, wpisz null (nie zgaduj!).
                    3. Status ustaw zawsze na "OK".
                    4. Zwróć tylko czysty kod JSON.
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        clean_text = odpowiedz.text.replace('```json', '').replace('```', '').strip()
                        dane_json = json.loads(clean_text)
                        wszystkie_dane.extend(dane_json)
                    except Exception as e:
                        st.error(f"Błąd przy {p.name}: {e}")

            if wszystkie_dane:
                df = pd.DataFrame(wszystkie_dane)
                # Sztywna kolejność kolumn zgodna z Twoim wzorem
                kolumny = ["Produkt", "Odmiana", "Masa netto", "Pochodzenie", "Klasa", "Liczba sztuk", "Wielkość", "Identyfikacja", "NRDD", "Status", "Opis"]
                df = df.reindex(columns=kolumny)
                
                st.subheader("Podgląd (Sprawdź czy kolumny są równe):")
                st.table(df) # Używamy st.table dla lepszej czytelności
                
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz poprawny Excel", csv, "dostawy_stabilne.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Problem techniczny: {e}")
