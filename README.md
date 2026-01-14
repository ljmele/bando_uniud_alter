# Uniud Albo Scraper & Telegram Bot 🎓🤖

Questo progetto automatizza il monitoraggio dell'[Albo Ufficiale dell'Università di Udine](https://www.uniud.it/it/albo-ufficiale).

Uno script Python controlla periodicamente la presenza di nuovi bandi, filtra quelli di interesse (basandosi su parole chiave e dipartimento) e invia una notifica immediata su **Telegram**.

## ✨ Funzionalità

- **Scraping Automatico**: Scarica l'elenco dei bandi dall'Albo ufficiale.
- **Filtraggio Intelligente**:
  - Cerca parole chiave specifiche nell'oggetto (es. "genetica", "bios-14").
  - Filtra per Dipartimento richiedente (es. "DARU").
- **Notifiche Telegram**: Invia un messaggio formattato con link diretto al bando se i filtri vengono superati.
- **Heartbeat**: Invia un messaggio giornaliero ("Sono vivo") per confermare che il bot è attivo.
- **Memoria Storica**: Salva gli ID dei bandi già analizzati in [`storia.json`](storia.json) per evitare notifiche doppie.
- **Zero Server**: Gira interamente su **GitHub Actions** (gratuitamente) ogni 5 minuti.

## 📂 Struttura del Progetto

- [`main.py`](main.py): Lo script principale. Esegue lo scraping, applica i filtri, gestisce la logica di notifica e aggiorna lo storico.
- [`bando_debug.py`](bando_debug.py): Script di utilità per testare la logica su un bando specifico (tramite ID) senza inviare notifiche reali. Utile per capire perché un bando è stato ignorato.
- [`storia.json`](storia.json): Un file JSON che funge da database, contenente la lista degli ID dei bandi già processati.
- [`.github/workflows/scraper.yml`](.github/workflows/scraper.yml): La configurazione di GitHub Actions. Definisce la pianificazione (ogni 5 minuti) e l'ambiente di esecuzione (Python, dipendenze).

## ⚙️ Configurazione

### Modificare i Filtri
Per cambiare cosa cercare, modifica le variabili all'inizio di [`main.py`](main.py):

```python
# Parole chiave (nell'oggetto, case-insensitive)
KEYWORDS = ["genetica", "bios-14"]

# Dipartimenti (nel richiedente, se vuoto [] cerca in tutti)
DIPARTIMENTI_TARGET = ["DARU"]
```

### GitHub Actions e Segreti
Il bot funziona grazie ai **GitHub Secrets** per proteggere le chiavi di Telegram. Per farlo funzionare nel tuo repository:

1. Vai su **Settings** del repository GitHub.
2. Vai su **Secrets and variables** > **Actions**.
3. Aggiungi i seguenti **Repository secrets**:
   - `TELEGRAM_TOKEN`: Il token fornito da @BotFather.
   - `TELEGRAM_CHAT_ID`: L'ID della chat (o del canale) dove vuoi ricevere i messaggi.

## 🚀 Esecuzione Locale

Se vuoi testare il bot sul tuo computer:

1. **Installa le dipendenze**:
   ```bash
   pip install requests beautifulsoup4
   ```

2. **Imposta le variabili d'ambiente** (oppure modificale provvisoriamente nel codice):
   - Linux/Mac: `export TELEGRAM_TOKEN="tuo_token"`, `export TELEGRAM_CHAT_ID="tuo_id"`
   - Windows (PowerShell): `$env:TELEGRAM_TOKEN="tuo_token"`, etc.

3. **Esegui lo script**:
   ```bash
   python main.py
   ```

## 🐞 Debugging
Se un bando non è stato notificato, usa [`bando_debug.py`](bando_debug.py).
Modifica la variabile `TARGET_ID` all'interno del file con il numero del bando problematico ed eseguilo:
```bash
python bando_debug.py
```
Ti mostrerà esattamente come viene letto dal sito e perché i filtri lo hanno scartato (o accettato).

---
*Bot creato per scopi didattici e di utilità personale.*