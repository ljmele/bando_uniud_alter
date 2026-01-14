import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import html  # Importante per pulire i testi

# --- CONFIGURAZIONE ---
URL_ALBO = "https://www.uniud.it/it/albo-ufficiale"
FILE_STORIA = "storia.json"

# Parole chiave (tutto minuscolo)
KEYWORDS = ["genetica", "bios-14"]

# Dipartimenti nel RICHIEDENTE (Se vuoto [], ignora il filtro)
DIPARTIMENTI_TARGET = ["DARU"]

def invia_telegram(messaggio):
    """Invia il messaggio al tuo bot Telegram usando HTML."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Errore: Token o Chat ID mancanti.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # MODIFICA 1: Usiamo HTML invece di Markdown per evitare errori con caratteri come _ o *
    payload = {
        "chat_id": chat_id,
        "text": messaggio,
        "parse_mode": "HTML", 
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Solleva un'eccezione se Telegram risponde con errore (es. 400)
    except Exception as e:
        print(f"ERRORE INVIO TELEGRAM: {e}")
        # Se possibile, stampiamo la risposta di Telegram per capire il perché
        try: print(response.text)
        except: pass

def battito_cardiaco():
    """Invia un messaggio di 'Sono Vivo' una volta al giorno."""
    ora_adesso = datetime.now()
    ORA_TARGET_UTC = 7
    
    if ora_adesso.hour == ORA_TARGET_UTC and 0 <= ora_adesso.minute < 30:
        # MODIFICA 2: Sintassi HTML
        messaggio = (
            f"🔊 <b>HEARTBEAT GIORNALIERO</b>\n"
            f"Il sistema è attivo.\n"
            f"Orario: {ora_adesso.strftime('%H:%M')}"
        )
        invia_telegram(messaggio)
        print("Heartbeat inviato.")

def carica_storia():
    if not os.path.exists(FILE_STORIA):
        return []
    with open(FILE_STORIA, 'r') as f:
        try: return json.load(f)
        except json.JSONDecodeError: return []

def salva_storia(nuova_lista_id):
    with open(FILE_STORIA, 'w') as f:
        json.dump(nuova_lista_id, f)

def estrai_dati(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tabella = soup.find("table", class_="table_albo")
    
    if not tabella:
        # Questo è l'errore che hai visto nei log ieri
        print("Attenzione: Tabella 'table_albo' non trovata nella pagina.")
        return []

    bandi_trovati = []
    tbody = tabella.find("tbody")
    if tbody:
        righe = tbody.find_all("tr")
        for riga in righe:
            colonne = riga.find_all("td")
            if len(colonne) < 4: continue 

            numero_id = colonne[0].get_text(strip=True)
            data_reg = colonne[1].get_text(strip=True)
            
            cella_oggetto = colonne[2]
            link_elem = cella_oggetto.find("a")
            oggetto_testo = link_elem.get_text(strip=True) if link_elem else cella_oggetto.get_text(strip=True)
            link_url = link_elem['href'] if link_elem else ""

            richiedente_testo = colonne[3].get_text(strip=True)

            bandi_trovati.append({
                "id": numero_id,
                "data": data_reg,
                "oggetto": oggetto_testo,
                "richiedente": richiedente_testo,
                "link": link_url
            })
            
    return bandi_trovati

def main():
    print(f"--- Esecuzione {datetime.now()} ---")
    battito_cardiaco()

    try:
        response = requests.get(URL_ALBO, timeout=20)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"Errore connessione al sito Uniud: {e}")
        return

    ids_vecchi = carica_storia()
    print(f"Bandi in memoria: {len(ids_vecchi)}")

    bandi_attuali = estrai_dati(html_content)
    print(f"Bandi trovati online: {len(bandi_attuali)}")

    if not bandi_attuali:
        print("Nessun bando estratto. Possibile errore di parsing o sito vuoto.")
        # Se non trovo nulla, NON salvo la storia per sicurezza, 
        # per evitare di cancellare la memoria se il sito è down.
        return 

    ids_attuali = [b['id'] for b in bandi_attuali]
    nuovi_bandi = []

    for bando in bandi_attuali:
        if bando['id'] not in ids_vecchi:
            nuovi_bandi.append(bando)

            # --- FILTRI ---
            oggetto_lower = bando['oggetto'].lower()
            richiedente_upper = bando['richiedente'].upper()
            
            key_interessante = False
            dip_interessante = False

            for parola in KEYWORDS:
                if parola in oggetto_lower:
                    key_interessante = True
                    break

            if not DIPARTIMENTI_TARGET:
                dip_interessante = True
            else:
                for dip in DIPARTIMENTI_TARGET:
                    if dip in richiedente_upper:
                        dip_interessante = True
                        break
            
            if key_interessante and dip_interessante:
                # MODIFICA 3: Costruzione messaggio con tag HTML
                # Usiamo html.escape per evitare che < o > nel testo rompano l'HTML
                ogg_safe = html.escape(bando['oggetto'])
                rich_safe = html.escape(bando['richiedente'])
                
                msg = (f"🚨 <b>NUOVO BANDO RILEVATO!</b> 🚨\n\n"
                       f"🏢 <b>Da:</b> {rich_safe}\n"
                       f"📄 <b>Oggetto:</b> {ogg_safe}\n\n"
                       f"🔗 <a href='{bando['link']}'>Link al bando</a>")
                
                invia_telegram(msg)
                print(f"Notifica inviata per: {bando['id']}")
            else:
                print(f"Nuovo bando {bando['id']} ignorato (Filtri non passati).")

    # Aggiornamento Memoria
    # Salviamo solo se abbiamo trovato qualcosa, per evitare di sovrascrivere con liste vuote in caso di errori
    if len(ids_attuali) > 0:
        salva_storia(ids_attuali)
        if nuovi_bandi:
            print(f"Storico aggiornato con {len(nuovi_bandi)} nuovi arrivi.")
        else:
            print("Storico aggiornato (nessuna novità rilevante).")

if __name__ == "__main__":
    main()