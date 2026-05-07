import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json

st.set_page_config(page_title="Fresh World - System Danych Wejściowych", layout="wide")
st.title("📦 Generator Składników Arkusza (Zgodny z Formułą)")

api_key = st.sidebar.text_input("Klucz API:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia etykiet:", accept_multiple_files=True)

        if st.button("🚀 WYGENERUJ SKŁADNIKI"):
            wszystkie_wyniki = []
            
            for p in pliki:
                with st.spinner(f"Analiza: {p.name}..."):
                    obraz = Image.open(p)
                    
                    # ZAKTUALIZOWANE ZASADY: WIELKIE LITERY I FORMAT KLASY
                    zadanie = """
                    Zanalizuj zdjęcie i zwróć dane jako LISTA JSON.
                    Mapowanie danych do Twoich kolumn Excel:
                    "E": Produkt (np. MANGO)
                    "F": Kolor miąższu (jeśli jest, np. ŻÓŁTY)
                    "G": Odmiana (np. PALMER)
                    "H": Masa netto (np. 3kg, 10x500g - ZACHOWAJ MAŁE LITERY)
                    "I": Pochodzenie (Kraj, np. BRAZYLIA)
                    "J": Klasa (Zawsze dodaj przedrostek 'KL', np. 'KL I', 'KL II', 'KL 1')
                    "K": Liczba sztuk (np. 8X2)
                    "L": Wielkość (np. 48-57MM)
                    "M": Identyfikacja (Nr dostawy P/I)
                    "N": NRDD (Numer NRDD)
                    
                    ZASADY BEZWZGLĘDNE:
                    1. WSZYSTKIE dane (oprócz kolumny H) muszą być zapisane WIELKIMI LITERAMI.
                    2. Kolumna "H" (Masa netto) musi pozostać w formacie z małymi literami (np. kg, g).
                    3. Kolumna "J" (Klasa) MUSI zaczynać się od "KL " (np. KL I).
                    4. NIE używaj słowa FRESHWORLD.
                    5. Jeśli brak danych, wpisz "".
                    6. Zwróć tylko czysty JSON.
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        clean_json = odpowiedz.text.replace('```json', '').replace('```', '').strip()
                        dane = json.loads(clean_json)
                        
                        # Dodatkowe zabezpieczenie formatowania w Pythonie
                        for rekord in dane:
                            for klucz in rekord:
                                if klucz == "H": # Masa netto zostaje jak jest
                                    pass
                                elif rekord[klucz]: # Reszta na wielkie litery
                                    rekord[klucz] = str(rekord[klucz]).upper()
                        
                        wszystkie_wyniki.extend(dane)
                    except Exception as e:
                        st.error(f"Błąd pliku {p.name}: {e}")

            if wszystkie_wyniki:
                df = pd.DataFrame(wszystkie_wyniki)
                # Ustalenie kolejności kolumn dokładnie pod Twój arkusz
                df = df.reindex(columns=["E", "F", "G", "H", "I", "J", "K", "L", "M", "N"])
                
                # Zmiana nazw tylko na potrzeby wyświetlania
                df.columns = ["Produkt (E)", "Kolor (F)", "Odmiana (G)", "Masa (H)", "Kraj (I)", "Klasa (J)", "Sztuki (K)", "Wielkość (L)", "ID (M)", "NRDD (N)"]
                
                st.subheader("Podgląd danych (Gotowe do wklejenia):")
                st.dataframe(df)
                
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz dane do wklejenia", csv, "dane_wejsciowe.csv", "text/csv")
                
    except Exception as e:
        st.error(f"Błąd: {e}")
