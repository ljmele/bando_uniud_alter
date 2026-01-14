import requests
from bs4 import BeautifulSoup

# --- CONFIGURAZIONE DEBUG ---
URL_ALBO = "https://www.uniud.it/it/albo-ufficiale"
TARGET_ID = "31"  # <--- INSERISCI QUI IL NUMERO ID DEL BANDO CHE NON TI È ARRIVATO

# I tuoi filtri attuali
KEYWORDS = ["genetica", "bios-14"]
DIPARTIMENTI_TARGET = ["DARU"]

def debug_analisi():
    print(f"--- DEBUG ANALISI ID: {TARGET_ID} ---")
    try:
        response = requests.get(URL_ALBO, timeout=15)
        html_content = response.text
    except Exception as e:
        print(f"Errore connessione: {e}")
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    tabella = soup.find("table", class_="table_albo")
    if not tabella:
        print("Tabella non trovata!")
        return

    tbody = tabella.find("tbody")
    if not tbody: return

    trovato = False
    righe = tbody.find_all("tr")

    for riga in righe:
        colonne = riga.find_all("td")
        if len(colonne) < 4: continue

        numero_id = colonne[0].get_text(strip=True)

        # Cerchiamo SOLO il bando incriminato
        if numero_id == TARGET_ID:
            trovato = True
            
            # Estrazione dati grezzi
            cella_oggetto = colonne[2]
            link_elem = cella_oggetto.find("a")
            oggetto_testo = link_elem.get_text(strip=True) if link_elem else cella_oggetto.get_text(strip=True)
            richiedente_testo = colonne[3].get_text(strip=True)
            
            print(f"\n1. DATI ESTRATTI DAL SITO:")
            print(f"   - Oggetto: '{oggetto_testo}'")
            print(f"   - Richiedente: '{richiedente_testo}'")

            # Simulazione Logica Filtri
            oggetto_lower = oggetto_testo.lower()
            richiedente_upper = richiedente_testo.upper()

            print(f"\n2. ANALISI LOGICA:")
            
            # Test Keywords
            key_interessante = False
            match_word = ""
            for parola in KEYWORDS:
                if parola in oggetto_lower:
                    key_interessante = True
                    match_word = parola
                    break
            print(f"   - Check KEYWORDS ({KEYWORDS}): {'✅ PASSATO' if key_interessante else '❌ FALLITO'}")
            if key_interessante:
                print(f"     (Trovata parola: '{match_word}')")

            # Test Dipartimento
            dip_interessante = False
            match_dip = ""
            if not DIPARTIMENTI_TARGET:
                dip_interessante = True
                print("   - Check DIPARTIMENTI: ✅ PASSATO (Lista vuota = accetta tutto)")
            else:
                for dip in DIPARTIMENTI_TARGET:
                    if dip in richiedente_upper:
                        dip_interessante = True
                        match_dip = dip
                        break
                print(f"   - Check DIPARTIMENTI ({DIPARTIMENTI_TARGET}): {'✅ PASSATO' if dip_interessante else '❌ FALLITO'}")
                if dip_interessante:
                    print(f"     (Trovato dipartimento: '{match_dip}' in '{richiedente_upper}')")
                else:
                    print(f"     (Confrontato '{richiedente_upper}' con lista {DIPARTIMENTI_TARGET})")

            # Verdetto Finale
            if key_interessante and dip_interessante:
                print("\n3. RISULTATO FINALE: 🚀 SAREBBE PARTITA LA NOTIFICA")
            else:
                print("\n3. RISULTATO FINALE: 🔇 SAREBBE STATO IGNORATO")
            
            break
    
    if not trovato:
        print(f"Bando ID {TARGET_ID} non trovato nella pagina (forse è passato in seconda pagina o è stato rimosso).")

if __name__ == "__main__":
    debug_analisi()