import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

st.set_page_config(page_title="System Dostaw Fresh World", layout="wide")
st.title("📊 Zaawansowany Generator Arkusza Dostaw")

with st.sidebar:
    st.header("Konfiguracja")
    api_key = st.text_input("Klucz API:", type="password")
    st.info("System przygotowany pod pełną strukturę arkusza Excel.")

if api_key:
    try:
        genai.configure(api_key=api_key)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia etykiet:", accept_multiple_files=True)

        if st.button("🚀 GENERUJ PEŁNY ARKUSZ"):
            wszystkie_wiersze = []
            
            for p in pliki:
                with st.spinner(f"Przetwarzanie: {p.name}..."):
                    obraz = Image.open(p)
                    
                    # PRECYZYJNY PROMPT DLA STRUKTURY EXCEL
                    zadanie = """
                    Zanalizuj etykiety i zwróć dane w formacie CSV, używając średnika (;) jako separatora.
                    Dla każdego produktu na zdjęciu stwórz jeden wiersz.
                    
                    KOLUMNY DO WYPELNIENIA (W TEJ KOLEJNOSCI):
                    1. Produkt (np. MANGO, LIMONKI)
                    2. Odmiana (np. PALMER, FUERTE - jeśli brak, zostaw puste)
                    3. Masa netto (np. 3KG, 6KG, 10X500G)
                    4. Pochodzenie (Kraj)
                    5. Klasa (np. 1, I, EXTRA)
                    6. Liczba sztuk (np. 8X2, 16X6 - jeśli brak, zostaw puste)
                    7. Wielkość (np. 48-57 MM, 90-105 G)
                    8. Identyfikacja produktu (Numer dostawy np. P:15058/26 lub I:93688)
                    9. NRDD (Odczytaj numer NRDD, np. 41426. Jeśli brak, zostaw puste)
                    10. Status (Zawsze wpisz: OK)
                    11. Opis (Pełna nazwa z etykiety dla sprawdzenia)

                    ZASADY:
                    - NIE używaj słów 'PRODUKT:', 'KRAJ:' itp.
                    - NIE używaj słowa 'FRESHWORLD'.
                    - Jeśli danej informacji nie ma na etykiecie, zostaw puste pole między średnikami.
                    - Wszystko WIELKIMI LITERAMI.
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        linie = odpowiedz.text.strip().split('\n')
                        
                        for linia in linie:
                            if ";" in linia:
                                dane = linia.split(";")
                                if len(dane) >= 8: # Minimalna walidacja
                                    wszystkie_wiersze.append({
                                        "Produkt": dane[0].strip(),
                                        "Odmiana": dane[1].strip(),
                                        "Masa netto": dane[2].strip(),
                                        "Pochodzenie": dane[3].strip(),
                                        "Klasa": dane[4].strip(),
                                        "Liczba sztuk": dane[5].strip(),
                                        "Wielkość": dane[6].strip(),
                                        "Identyfikacja produktu": dane[7].strip(),
                                        "NRDD": dane[8].strip() if len(dane)>8 else "",
                                        "Status": "OK",
                                        "Opis": dane[10].strip() if len(dane)>10 else ""
                                    })
                    except Exception as e:
                        st.error(f"Błąd pliku {p.name}: {e}")

            if wszystkie_wiersze:
                df = pd.DataFrame(wszystkie_wiersze)
                st.subheader("Podgląd arkusza")
                st.dataframe(df, use_container_width=True)
                
                # Generowanie pliku do pobrania
                csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 Pobierz gotowy arkusz Excel (CSV)", csv, "arkusz_dostaw.csv", "text/csv")

    except Exception as e:
        st.error(f"Błąd systemu: {e}")
else:
    st.warning("Wklej swój Klucz API, aby połączyć się z systemem.")
