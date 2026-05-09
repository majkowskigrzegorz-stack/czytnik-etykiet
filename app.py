import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io
import zipfile

# ==========================================
# USTAWIENIA STRONY
# ==========================================
st.set_page_config(page_title="Czytnik Etykiet Fresh World PRO", layout="wide")
st.title("📦 Generator Danych z Formułą Opisu")

st.markdown("### ⭐ Wersja: FRESH_WORLD_FORMULA_2026")

with st.sidebar:
    st.header("Konfiguracja")
    api_key = st.text_input("Wklej Klucz API Google:", type="password")
    st.info("System generuje teraz automatyczną formułę łączącą w pierwszej kolumnie.")

if api_key:
    try:
        genai.configure(api_key=api_key)
        modele = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        wybrany_model = next((m for m in modele if "flash" in m), modele[0])
        model = genai.GenerativeModel(wybrany_model)

        pliki = st.file_uploader("Wgraj zdjęcia etykiet:", accept_multiple_files=True)

        if st.button("🚀 ODCZYTAJ I GENERUJ"):
            wszystkie_wyniki = []
            
            for p in pliki:
                with st.spinner(f"Analizuję: {p.name}..."):
                    obraz = Image.open(p)
                    
                    zadanie = """
                    Odczytaj dane ze wszystkich etykiet na zdjęciu i zwróć je WYŁĄCZNIE jako listę obiektów JSON.
                    Skup się na ETYKIETACH ZBIORCZECH (mnożniki np. '8x1,5 kg').

                    Klucze JSON:
                    "E": Produkt
                    "F": Kolor miąższu
                    "G": Odmiana
                    "H": Masa netto
                    "I": Pochodzenie
                    "J": Klasa
                    "K": Sztuki/Opakowanie
                    "L": Wielkość
                    "M": Identyfikacja
                    "N": NRDD
                    
                    ZASADY:
                    1. Ignoruj słowo FRESHWORLD.
                    2. Mnożniki (x) zawsze do kolumny K (małe litery).
                    3. Masa całkowita (H) pusta, jeśli jest mnożnik w K.
                    4. Wielkość (L) małe litery, bez spacji.
                    """
                    
                    try:
                        odpowiedz = model.generate_content([zadanie, obraz])
                        clean_json = odpowiedz.text.replace('```json', '').replace('```', '').strip()
                        dane_z_etykiet = json.loads(clean_json)
                        
                        for etykieta in dane_z_etykiet:
                            # Przetwarzanie wartości
                            for klucz in etykieta:
                                val = str(etykieta[klucz]).strip() if etykieta[klucz] is not None else ""
                                if klucz == "L":
                                    etykieta[klucz] = val.lower().replace(" ", "")
                                elif klucz == "K":
                                    etykieta[klucz] = val.lower()
                                elif klucz == "H":
                                    etykieta[klucz] = val.lower()
                                else:
                                    etykieta[klucz] = val.upper()
                            
                            if "x" in etykieta.get("K", ""):
                                etykieta["H"] = ""

                            klasa = etykieta.get("J", "")
                            if klasa and not klasa.startswith("KL "):
                                etykieta["J"] = f"KL {klasa.replace('KL', '').strip()}"

                        wszystkie_wyniki.extend(dane_z_etykiet)
                    except:
                        pass

            if wszystkie_wyniki:
                df = pd.DataFrame(wszystkie_wyniki)
                # Kolejność kolumn zgodna z Twoim mapowaniem
                kolejnosc = ["E", "G", "L", "F", "K", "I", "H", "J", "M", "N"]
                df = df.reindex(columns=kolejnosc).fillna("")
                
                # Dodawanie kolumny Opis z formułą Excela
                # Formuła odnosi się do kolumn od B do I (Produkt do Klasa) dla wiersza n+2 (bo nagłówek)
                def stworz_formule(row_idx):
                    r = row_idx + 2
                    return f'=USUŃ.ZBĘDNE.ODSTĘPY(JEŻELI(B{r}<>"";B{r}&" ";"")&JEŻELI(C{r}<>"";C{r}&" ";"")&JEŻELI(D{r}<>"";D{r}&" ";"")&JEŻELI(E{r}<>"";E{r}&" ";"")&JEŻELI(F{r}<>"";F{r}&" ";"")&JEŻELI(G{r}<>"";G{r}&" ";"")&JEŻELI(H{r}<>"";H{r}&" ";"")&JEŻELI(I{r}<>"";I{r}&" ";""))'

                df.insert(0, "Opis", [stworz_formule(i) for i in range(len(df))])

                df.columns = [
                    "Opis", "Produkt", "Odmiana", "Wielkość", "Kolor miąższu", 
                    "Sztuki", "Kraj", "Masa netto", "Klasa", "Identyfikacja", "NRDD"
                ]
                
                st.success("Analiza zakończona!")
                st.dataframe(df, use_container_width=True)
                
                csv_buffer = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button("💾 POBIERZ CSV", csv_buffer.encode('utf-8-sig'), "dane.csv", "text/csv")
                with col2:
                    zip_out = io.BytesIO()
                    with zipfile.ZipFile(zip_out, "a", zipfile.ZIP_DEFLATED, False) as zf:
                        zf.writestr("dane_freshworld.csv", csv_buffer.encode('utf-8-sig'))
                    st.download_button("📦 POBIERZ ZIP", zip_out.getvalue(), "dane.zip", "application/zip")
                
    except Exception as e:
        st.error(f"Błąd: {e}")
