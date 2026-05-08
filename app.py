import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json

st.set_page_config(page_title="Czytnik Etykiet Fresh World", layout="wide")
st.title("📦 Kompletny Generator Danych do Excela")

with st.sidebar:
    st.header("Konfiguracja")
    api_key = st.text_input("Wklej Klucz API Google:", type="password")
    st.info("System jest skonfigurowany pod Twoją formułę Excela i układ kolumn.")

if api_key:
    try:
        genai.configure(api_key=api_key)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia etykiet (możesz zaznaczyć kilka):", accept_multiple_files=True)

        if st.button("🚀 ODCZYTAJ I WYGENERUJ TABELĘ"):
            wszystkie_wyniki = []
            
            for p in pliki:
                with st.spinner(f"Analizuję arkusz: {p.name}..."):
                    obraz = Image.open(p)
                    
                    # PROMPT: Nacisk na etykiety zbiorcze i ignorowanie sumarycznej masy netto
                    zadanie = """
                    Odczytaj dane ze wszystkich etykiet na zdjęciu i zwróć je WYŁĄCZNIE jako listę obiektów JSON.
                    Zwróć szczególną uwagę na ETYKIETY ZBIORCZE (całego kartonu), które zawierają mnożnik (np. '8x1,5 kg', '12x250 g').

                    Użyj dokładnie tych kluczy (litery odpowiadają późniejszemu mapowaniu):
                    "E": Produkt (np. CYTRYNA, POMIDORY KOKTAJLOWE CZERWONE - bez gramatury/mnożnika w nazwie!)
                    "F": Kolor miąższu (jeśli jest)
                    "G": Odmiana (np. PRIMOFIORI)
                    "H": Masa netto (Wpisuj TYLKO dla etykiet pojedynczych, np. '1500 g', '250 g'. Dla etykiet zbiorczych z mnożnikiem zostaw PUSTE "")
                    "I": Pochodzenie (Kraj, np. BRAZYLIA)
                    "J": Klasa
                    "K": Opakowanie zbiorcze / Sztuki (To najważniejsze pole dla etykiet zbiorczych! Wpisz dokładnie z etykiety, np. "8x1,5 kg", "12x250 g". Jeśli etykieta dotyczy tylko sztuk bez wagi, dopisz 'szt.', np. "10x2 szt.", "6 szt.")
                    "L": Wielkość (np. 48-57MM)
                    "M": Identyfikacja (Nr dostawy np. P:15058/26, I:93539)
                    "N": NRDD (Sam numer NRDD, np. 41426)
                    
                    ZASADY KRYTYCZNE:
                    1. NIE używaj w ogóle słowa "FRESHWORLD" ani "FRESH WORLD".
                    2. Mnożniki (np. 8x1,5 kg) ZAWSZE lądują w kluczu "K". Masa całkowita (np. 12 kg) ma być wtedy ZIGNOROWANA ("H" ma być "").
                    3. Zwróć tylko surowy kod JSON. Żadnych wstępów.
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        clean_json = odpowiedz.text.replace('```json', '').replace('```', '').strip()
                        dane_z_etykiet = json.loads(clean_json)
                        
                        for etykieta in dane_z_etykiet:
                            for klucz in etykieta:
                                wartosc = str(etykieta[klucz]).strip() if etykieta[klucz] is not None else ""
                                
                                if klucz == "H":
                                    etykieta[klucz] = wartosc.lower()
                                elif klucz == "L":
                                    # Wielkość: małe litery i usunięcie spacji (np. "48-57mm")
                                    etykieta[klucz] = wartosc.lower().replace(" ", "")
                                elif klucz == "K":
                                    # Sztuki: wymuszenie małych liter (w tym mały 'x' i 'kg')
                                    etykieta[klucz] = wartosc.lower()
                                else:
                                    etykieta[klucz] = wartosc.upper()
                            
                            # Twarda reguła w Pythonie: Jeśli w kolumnie K (Sztuki) jest mnożnik 'x',
                            # wymuś absolutne wyczyszczenie kolumny H (Masa netto), aby nie pobrać zsumowanych 12 kg
                            if "x" in etykieta.get("K", ""):
                                etykieta["H"] = ""

                            # Formatowanie Klasy do postaci np. "KL I"
                            wartosc_j = etykieta.get("J", "")
                            if wartosc_j and not wartosc_j.startswith("KL "):
                                wartosc_j = wartosc_j.replace("KL", "").strip()
                                etykieta["J"] = f"KL {wartosc_j}"

                        wszystkie_wyniki.extend(dane_z_etykiet)
                        
                    except Exception as e:
                        st.error(f"Nie udało się przetworzyć pliku {p.name}. Szczegóły: {e}")

            if wszystkie_wyniki:
                df = pd.DataFrame(wszystkie_wyniki)
                
                nowa_kolejnosc = ["E", "G", "L", "F", "K", "I", "H", "J", "M", "N"]
                df = df.reindex(columns=nowa_kolejnosc).fillna("")
                
                df.columns = [
                    "Produkt (A)", "Odmiana (B)", "Wielkość (C)", "Kolor miąższu (D)", 
                    "Sztuki (F)", "Kraj (G)", "Masa netto (H)", "Klasa (I)", "Identyfikacja (J)", "NRDD (K)"
                ]
                
                st.success(f"Analiza zakończona! Odnaleziono {len(wszystkie_wyniki)} etykiet.")
                
                st.dataframe(df, use_container_width=True)
                
                csv_data = df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="💾 POBIERZ PLIK DO EXCELA (.csv)", 
                    data=csv_data, 
                    file_name="dane_freshworld.csv", 
                    mime="text/csv"
                )
                
    except Exception as e:
        st.error(f"Błąd konfiguracji lub serwera: {e}")
else:
    st.info("👈 Aby rozpocząć, wklej swój Klucz API w panelu po lewej stronie.")
