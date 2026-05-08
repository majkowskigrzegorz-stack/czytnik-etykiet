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
                    
                    zadanie = """
                    Odczytaj dane ze wszystkich etykiet na zdjęciu i zwróć je WYŁĄCZNIE jako listę obiektów JSON.
                    Każdy obiekt to jedna etykieta. Użyj dokładnie tych kluczy (litery odpowiadają późniejszemu mapowaniu):
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
                                else:
                                    etykieta[klucz] = wartosc.upper()
                            
                            wartosc_j = etykieta.get("J", "")
                            if wartosc_j and not wartosc_j.startswith("KL "):
                                wartosc_j = wartosc_j.replace("KL", "").strip()
                                etykieta["J"] = f"KL {wartosc_j}"

                        wszystkie_wyniki.extend(dane_z_etykiet)
                        
                    except Exception as e:
                        st.error(f"Nie udało się przetworzyć pliku {p.name}. Szczegóły: {e}")

            if wszystkie_wyniki:
                df = pd.DataFrame(wszystkie_wyniki)
                
                # Ustalenie dokładnej kolejności zgodnej z Twoim zdjęciem Excela
                nowa_kolejnosc = ["E", "G", "L", "F", "K", "I", "H", "J", "M", "N"]
                df = df.reindex(columns=nowa_kolejnosc).fillna("")
                
                # Nadanie dokładnych nazw nagłówkom
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
