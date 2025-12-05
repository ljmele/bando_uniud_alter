import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# --- CONFIGURAZIONE ---
URL_ALBO = "https://www.uniud.it/it/albo-ufficiale"
FILE_STORIA = "storia.json" # Il file che funge da "memoria"

# Parole chiave che ti interessano (tutto minuscolo per facilitare il confronto)
KEYWORDS = ["genetica", "bios-14"]

# Nuova lista: Sigle dei Dipartimenti nel RICHIEDENTE che vuoi monitorare
# (Se lasci questa lista vuota [], il filtro verrà ignorato)
DIPARTIMENTI_TARGET = ["DARU"]

def invia_telegram(messaggio):
    """Invia il messaggio al tuo bot Telegram."""
    # Recuperiamo i segreti dall'ambiente (NON SCRIVERLI QUI!)
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Errore: Token o Chat ID mancanti nelle variabili d'ambiente.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": messaggio,
        "parse_mode": "Markdown" # Per mettere in grassetto o corsivo
    }
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def battito_cardiaco():
    """
    Invia un messaggio di 'Sono Vivo' una volta al giorno.
    Sfrutta il fatto che lo script gira spesso.
    """
    ora_adesso = datetime.now()
    
    # --- CONFIGURAZIONE ORARIO HEARTBEAT ---
    # GitHub usa l'orario UTC (Londra). L'Italia è UTC+1 (inverno) o UTC+2 (estate).
    # Se metti hour=7, in Italia riceverai il messaggio alle 08:00 o 09:00.
    ORA_TARGET_UTC = 6 
    
    # Controlliamo se siamo nell'ora giusta E nei primi 15 minuti dell'ora.
    # Siccome il tuo cron gira ogni 10 o 15 minuti, questo accadrà una sola volta al giorno.
    if ora_adesso.hour == ORA_TARGET_UTC and 0 <= ora_adesso.minute < 15:
        messaggio = (
            f"💓 **HEARTBEAT GIORNALIERO**\n"
            f"Il sistema è attivo e funzionante.\n"
            f"Orario server: {ora_adesso.strftime('%H:%M')}"
        )
        invia_telegram(messaggio)
        print("Heartbeat inviato.")

def carica_storia():
    """Carica gli ID dei bandi già visti dal file JSON."""
    if not os.path.exists(FILE_STORIA):
        return []
    with open(FILE_STORIA, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salva_storia(nuova_lista_id):
    """Salva la lista aggiornata degli ID su file JSON."""
    with open(FILE_STORIA, 'w') as f:
        json.dump(nuova_lista_id, f)

def estrai_dati(html):
    """Analizza l'HTML e restituisce una lista di dizionari (i bandi)."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Troviamo la tabella specifica usando la classe che abbiamo visto nel tuo file
    tabella = soup.find("table", class_="table_albo")
    
    if not tabella:
        print("Errore: Tabella 'table_albo' non trovata.")
        return []

    bandi_trovati = []
    
    # 2. Iteriamo sulle righe del corpo tabella (tbody)
    # Saltiamo l'header, cerchiamo direttamente dentro tbody -> tr
    tbody = tabella.find("tbody")
    if tbody:
        righe = tbody.find_all("tr")
        
        for riga in righe:
            colonne = riga.find_all("td")
            if len(colonne) < 4: continue # Salta righe malformate

            # Estrazione dati basata sulla struttura del tuo HTML
            numero_id = colonne[0].get_text(strip=True) # Colonna "Numero"
            data_reg = colonne[1].get_text(strip=True)  # Colonna "Data registrazione"
            
            # Colonna "Oggetto": contiene il link e il testo
            cella_oggetto = colonne[2]
            link_elem = cella_oggetto.find("a")
            
            oggetto_testo = link_elem.get_text(strip=True) if link_elem else cella_oggetto.get_text(strip=True)
            link_url = link_elem['href'] if link_elem else ""

            richiedente_testo = colonne[3].get_text(strip=True) # Colonna "Richiedente"

            # Creiamo una "struct" (dizionario) per il bando
            bando = {
                "id": numero_id,
                "data": data_reg,
                "oggetto": oggetto_testo,
                "richiedente": richiedente_testo,
                "link": link_url
            }
            bandi_trovati.append(bando)
            
    return bandi_trovati

def main():
    print(f"--- Esecuzione {datetime.now()} ---")
    
    # 0. Controllo Battito Cardiaco (Prima di fare qualsiasi cosa)
    battito_cardiaco()

    # 1. Scarica HTML
    try:
        response = requests.get(URL_ALBO, timeout=15)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"Errore connessione: {e}")
        return

    # 2. Carica la memoria (i vecchi ID)
    ids_vecchi = carica_storia()
    print(f"Bandi in memoria: {len(ids_vecchi)}")

    # 3. Estrae i bandi attuali dalla pagina
    bandi_attuali = estrai_dati(html_content)
    print(f"Bandi trovati online: {len(bandi_attuali)}")

    # 4. Confronto (Logica del "Diff")
    ids_attuali = [b['id'] for b in bandi_attuali]
    nuovi_bandi = []

    for bando in bandi_attuali:
        if bando['id'] not in ids_vecchi:
            nuovi_bandi.append(bando)

            # --- IL FILTRO ---
            # Controlliamo se nell'oggetto c'è una parola che ci piace
            oggetto_lower = bando['oggetto'].lower()
            richiedente_upper = bando['richiedente'].upper() # Standardizziamo in maiuscolo
            
            key_interessante = False
            dip_interessante = False

            for parola in KEYWORDS:
                if parola in oggetto_lower:
                    key_interessante = True
                    break

            # 2. Check Dipartimento (solo se è già interessante)
            if key_interessante:
                for dip in DIPARTIMENTI_TARGET:
                    if dip in richiedente_upper:
                        dip_interessante = True
                        break
            
            # Se è interessante, invia notifica
            if key_interessante and dip_interessante:
                # Aggiungiamo il richiedente nel messaggio Telegram
                msg = (f"🚨 **NUOVO BANDO RILEVATO!** 🚨\n\n"
                       f"🏢 **Da:** {bando['richiedente']}\n"
                       f"📄 **Oggetto:** {bando['oggetto']}\n\n"
                       f"🔗 [Link al bando]({bando['link']})")
                
                invia_telegram(msg)
                print(f"Notifica inviata per: {bando['id']}")
            else:
                print(f"Nuovo bando {bando['id']} ignorato.")

    # 5. Aggiornamento Memoria
    if nuovi_bandi:
        print(f"Trovati {len(nuovi_bandi)} nuovi elementi. Aggiorno storico.")
        # Salviamo la nuova lista completa di ID per il prossimo giro
        salva_storia(ids_attuali)
    else:
        print("Nessun nuovo bando.")

if __name__ == "__main__":

    main()
