import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json

# ==========================================
# USTAWIENIA STRONY
# ==========================================
st.set_page_config(page_title="Czytnik Etykiet Fresh World", layout="wide")
st.title("📦 Kompletny Generator Danych do Excela")

# ==========================================
# PANEL BOCZNY - KONFIGURACJA
# ==========================================
with st.sidebar:
    st.header("Konfiguracja")
    api_key = st.text_input("Wklej Klucz API Google:", type="password")
    st.info("System jest skonfigurowany pod Twoją formułę Excela (kolumny E-N).")

# ==========================================
# GŁÓWNA LOGIKA APLIKACJI
# ==========================================
if api_key:
    try:
        # Logowanie do Google API
        genai.configure(api_key=api_key)
        
        # Automatyczne wyszukiwanie najlepszego modelu Flash (odporne na błędy 404)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia etykiet (możesz zaznaczyć kilka):", accept_multiple_files=True)

        if st.button("🚀 ODCZYTAJ I WYGENERUJ TABELĘ"):
            wszystkie_wyniki = []
            
            for p in pliki:
                with st.spinner(f"Analizuję arkusz: {p.name}..."):
                    obraz = Image.open(p)
                    
                    # PRECYZYJNY PROMPT DLA AI (Co ma odczytać i w jakim formacie)
                    zadanie = """
                    Odczytaj dane ze wszystkich etykiet na zdjęciu i zwróć je WYŁĄCZNIE jako listę obiektów JSON.
                    Każdy obiekt to jedna etykieta. Użyj dokładnie tych kluczy (odpowiadają kolumnom w Excelu):
                    "E": Produkt (np. MANGO)
                    "F": Kolor miąższu (jeśli jest, np. ŻÓŁTY)
                    "G": Odmiana (np. PALMER)
                    "H": Masa netto (np. 3kg, 10x500g - zachowaj małe litery dla jednostek)
                    "I": Pochodzenie (Kraj, np. BRAZYLIA)
                    "J": Klasa
                    "K": Liczba sztuk (np. 8X2)
                    "L": Wielkość (np. 48-57MM)
                    "M": Identyfikacja (Nr dostawy np. P:15058/26)
                    "N": NRDD (Sam numer NRDD, np. 41426)
                    
                    ZASADY KRYTYCZNE:
                    1. NIE używaj w ogóle słowa "FRESHWORLD" ani "FRESH WORLD". Jeśli je widzisz, zignoruj.
                    2. Jeśli na etykiecie brakuje jakiejś informacji, wpisz pusty ciąg znaków "".
                    3. Nie dodawaj żadnych innych kluczy (np. nie twórz kolumny Opis).
                    4. Zwróć tylko surowy kod JSON. Żadnych wstępów i zakończeń tekstowych.
                    """
                    
                    try:
                        # Wywołanie AI
                        odpowiedz = model.generate_content([zadanie, obraz])
                        
                        # Czyszczenie i parsowanie JSON
                        clean_json = odpowiedz.text.replace('```json', '').replace('```', '').strip()
                        dane_z_etykiet = json.loads(clean_json)
                        
                        # ==========================================
                        # ŻELAZNA LOGIKA FORMATOWANIA W PYTHONIE
                        # ==========================================
                        for etykieta in dane_z_etykiet:
                            for klucz in etykieta:
                                wartosc = str(etykieta[klucz]).strip() if etykieta[klucz] is not None else ""
                                
                                # Masa netto (H) -> małe litery
                                if klucz == "H":
                                    etykieta[klucz] = wartosc.lower()
                                # Cała reszta -> WIELKIE LITERY
                                else:
                                    etykieta[klucz] = wartosc.upper()
                            
                            # Klasa (J) -> Wymuszenie dopisku "KL "
                            wartosc_j = etykieta.get("J", "")
                            if wartosc_j and not wartosc_j.startswith("KL "):
                                # Czyścimy jeśli AI samo dodało samo "KL" bez spacji
                                wartosc_j = wartosc_j.replace("KL", "").strip()
                                etykieta["J"] = f"KL {wartosc_j}"

                        wszystkie_wyniki.extend(dane_z_etykiet)
                        
                    except Exception as e:
                        st.error(f"Nie udało się przetworzyć pliku {p.name}. Szczegóły: {e}")

            # ==========================================
            # GENEROWANIE TABELI I PLIKU POBIERANIA
            # ==========================================
            if wszystkie_wyniki:
                # Tworzenie ostatecznej tabeli Pandas
                df = pd.DataFrame(wszystkie_wyniki)
                
                # Wymuszamy rygorystyczną kolejność kolumn (E do N)
                kolumny_excel = ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N"]
                
                # Zabezpieczenie przed brakującymi kluczami - puste miejsca wypełniamy niczym ("")
                df = df.reindex(columns=kolumny_excel).fillna("")
                
                # Nadanie czytelnych nagłówków (tylko do wyświetlania na ekranie w aplikacji)
                df.columns = [
                    "Produkt (E)", "Kolor miąższu (F)", "Odmiana (G)", "Masa netto (H)", 
                    "Kraj (I)", "Klasa (J)", "Sztuki (K)", "Wielkość (L)", "Identyfikacja (M)", "NRDD (N)"
                ]
                
                st.success(f"Analiza zakończona! Odnaleziono {len(wszystkie_wyniki)} etykiet.")
                
                # Wyświetlanie gotowej tabeli
                st.dataframe(df, use_container_width=True)
