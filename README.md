# FAVERO FOOTBALL KIT CONTEST · V1

Streamlit + PostgreSQL cloud Supabase. Il voto viene salvato soltanto in cloud: nessun database locale, SQLite o file usato per conservare voti. La V1 è pronta da configurare; senza progetto Supabase e credenziali non può salvare voti. Non è ancora pubblicata.

## Sviluppo locale

Python 3.12 consigliato. Dalla cartella del progetto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/generate_password_hash.py
```

Il generatore chiede la password senza mostrarla: copia l'hash in `ADMIN_PASSWORD_HASH` del file `.env`. Configura `ADMIN_USERNAME=Paolo`, `SUPABASE_URL` e `SUPABASE_KEY`. Per la chiave usa la **legacy service_role** del progetto, esclusivamente lato server; non la anon/publishable. Non condividere questa chiave e non committare `.env` o `secrets.toml`.

## Supabase

1. Crea un progetto su Supabase e conserva la password del database.
2. Apri SQL Editor, incolla tutto `sql/schema.sql`, eseguilo **una sola volta su un progetto nuovo**. Lo script è transazionale e non cancella dati. Non eseguirlo su uno schema preesistente senza una migrazione.
3. Ottieni URL progetto e chiave legacy `service_role` dalle impostazioni API e inseriscili in `.env`.
4. Sono create `participants`, `sponsors`, `votes`, `contest_settings`, i sei sponsor iniziali e quattro RPC. RLS è abilitata senza accesso anonimo; la chiave server può leggere le tabelle ma le scritture applicative passano dalle RPC.
5. Avvia l'app e accedi ad Admin per aggiungere i partecipanti e assegnare le squadre. Nessun nominativo fittizio viene caricato automaticamente.

```powershell
python -m streamlit run app.py
```

Apri `http://localhost:8501`. Prova con un partecipante di test per ciascuna squadra: seleziona nome, sponsor, stemma e maglia, torna indietro, verifica riepilogo e conferma. Dopo refresh deve risultare già votato. Controlla risultati e CSV in Admin; gli sponsor della squadra votata devono risultare bloccati. Usa un progetto Supabase di prova: i voti definitivi non hanno un comando di reset nella UI.

## Asset da inserire

Gli asset non sono stati forniti. Pillow crea placeholder identificati come provvisori; non vengono inventate immagini Macron.

Stemmi in `assets/logos/`:

| File | Concept |
|---|---|
| energetici_fc.jpeg | ENERGETICI F.C. |
| renewables.jpeg | RENEWABLES |
| energentus.png | ENERGENTUS |
| rdm_fc.jpeg | RDM F.C. |
| rdm_world.jpeg | RDM WORLD |
| rdm_internazionale.jpeg | RDM INTERNAZIONALE |

Maglie originali Macron in ciascuna cartella `assets/kits/energetici_fc/`, `renewables/`, `energentus/`, `rdm_fc/`, `rdm_world/`, `rdm_internazionale/`. Ogni cartella identifica una delle tre proposte della squadra. Usa `01_frontale.jpg`, `02_retro.jpg`, `03_trequarti.jpg`, `04_dettaglio.jpg` (PNG/JPEG supportati). Aggiungi solo le viste disponibili: lo slider appare se sono più di una. Le cartelle sono mantenute in Git tramite `.gitkeep`.

Mockup in `assets/mockups/<kit>/` con gli stessi tipi immagine: hanno precedenza sulle maglie base. Per mockup di una combinazione specifica usa `assets/mockups/<kit>/<nome_concept>__<uuid_sponsor>/`. Questa cartella ha precedenza anche sul mockup generico. Il nome e lo stemma restano scelte indipendenti. La V1 non applica sponsor o stemmi automaticamente e non genera 3D.

## Deploy pubblico · GitHub + Streamlit Community Cloud

1. Crea un repository GitHub, preferibilmente privato. Prima del commit controlla che nessun segreto sia tracciato.
2. Dalla cartella, dopo aver installato Git:

```powershell
git init
git add .
git commit -m "V1 football kit contest"
git branch -M main
git remote add origin https://github.com/TUO_ACCOUNT/TUO_REPOSITORY.git
git push -u origin main
```

3. Accedi a Streamlit Community Cloud e collega GitHub. Crea un'app selezionando repository, branch `main`, entrypoint `app.py`, Python 3.12.
4. In Advanced settings / Secrets inserisci TOML:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_KEY = "YOUR_SERVER_SERVICE_ROLE_KEY"
ADMIN_USERNAME = "Paolo"
ADMIN_PASSWORD_HASH = "pbkdf2_sha256$600000$...$..."
```

5. Avvia deploy, attendi installazione e controlla i log. Ottieni l'URL `https://<nome-app>.streamlit.app`; scegli la visibilità desiderata nelle impostazioni. Provalo da smartphone e PC prima di distribuirlo ai colleghi.
6. Aggiornamenti: modifica i file, `git add .`, `git commit -m "Descrizione modifica"`, `git push`. Community Cloud aggiorna l'app; i voti rimangono in Supabase. Le modifiche allo schema richiedono migrazioni SQL separate: non rieseguire lo schema iniziale.

Documentazione: [deployment Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [Secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management), [funzioni Supabase](https://supabase.com/docs/guides/database/functions), [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security).

## Admin e integrità

Password PBKDF2 SHA-256 con salt casuale e 600.000 iterazioni. Sessione Admin di un'ora con logout e pausa tra tentativi falliti nella stessa sessione. Tutte le sezioni Admin richiedono login, compresi risultati e download. La pausa non costituisce rate limiting globale.

Il nome scelto dal menu **non autentica l'identità**: un collega potrebbe selezionare il nome di un altro. È il comportamento richiesto per questa V1; per una garanzia di identità occorre prima del lancio decidere se aggiungere PIN individuali o login aziendale. La chiave Supabase resta nel processo server, non nel browser.

La RPC del submit usa un lock transazionale condiviso con le operazioni Admin, deriva la squadra dal partecipante, valida scelte e sponsor, controlla apertura contest, inserisce il voto e aggiorna il partecipante atomicamente. `UNIQUE(participant_id)` protegge inoltre da duplicati. Se una risposta si perde dopo il commit, un nuovo tentativo restituisce già votato: controlla anche ricaricando la pagina. Refresh prima del submit può perdere la bozza in sessione, ma non i voti salvati. Le scritture dirette con un account proprietario del database restano operazioni amministrative esterne.

Export Admin: CSV UTF-8 con BOM, UUID, nominativi, scelte e timestamp UTC; le celle con prefissi formula sono neutralizzate. È un export dei voti, non un backup completo: per ripristino completo usa gli strumenti di backup PostgreSQL/Supabase e includi tutte le quattro tabelle. Conserva il CSV fuori dal repository.

## Verifica

```powershell
python -m pip install pytest
python -m pytest -q
python -m compileall -q app.py src pages scripts tests
```

I test locali usano un database fittizio in memoria solo nei test per esercitare UI, navigazione, errori e blocchi di accesso. L'app reale non usa questo database. Per verificare transazioni, privilegi e concorrenza reale esegui anche `sql/verify.sql` dopo lo schema in Supabase: usa una transazione e rollback, senza lasciare partecipanti/voti test. Il collaudo cloud multi-dispositivo richiede un Supabase configurato.

Il test di concorrenza separato si abilita con `python -m pytest -q --postgres-container NOME_CONTAINER`: richiede PostgreSQL isolato con schema già caricato e lascia un partecipante/voto di test nel solo container. Non usarlo contro il database del contest. Lo script `verify.sql` verifica l'integrità sequenziale; il test container verifica due invii simultanei.

## Prima del link ai colleghi

### Ottimizzazione delle selezioni

Il wizard riutilizza immagini decodificate e copie di visualizzazione compresse, senza ingrandire le sorgenti o modificare gli originali. Lo zoom conserva la risoluzione disponibile. Le miniature nella galleria servono solo alla navigazione; le immagini principali provengono dagli asset ad alta risoluzione.

Le 18 combinazioni nome/logo e maglia sono precalcolate in `assets/mockups/combinations/`. Dopo aver sostituito un logo o una maglia, esegui `python scripts/prepare_previews.py`: l'app verifica le impronte delle sorgenti e, se necessario, genera comunque la preview aggiornata. Pubblica anche questa cartella insieme al codice.

Partecipanti, apertura e sponsor nel wizard hanno una cache di 10 secondi, svuotata dopo il submit. Il controllo definitivo resta nella RPC Supabase a ogni invio; Admin e schema SQL non sono modificati. Il benchmark `python scripts/benchmark_selections.py` misura il rendering locale con database fittizio, senza registrare voti e senza includere il tempo di rete.

### Come ottenere il link pubblico

Supabase conserva i dati; il sito Streamlit va pubblicato separatamente. Crea un account GitHub e carica il progetto in un repository privato, poi accedi a [Streamlit Community Cloud](https://share.streamlit.io/) con GitHub. Seleziona **Create app**, il repository e `app.py`. Nelle impostazioni avanzate copia i valori del tuo `.env` nel formato Secrets mostrato sopra, senza caricare il file `.env` nel repository. Dopo il deploy ottieni un indirizzo `https://nome-app.streamlit.app` da condividere.

Prima di inviarlo ai colleghi, verifica quel link dal telefono e controlla nell'Admin che il contest sia aperto e che i partecipanti siano presenti. Il login Admin è riservato all'organizzatore. Il collaudo locale usa dati fittizi: il salvataggio sul sito pubblico va verificato separatamente prima della raccolta definitiva.

Configurare Supabase e Secrets; aggiungere partecipanti e asset originali autorizzati; scegliere il livello di identificazione; verificare salvataggio reale, doppio invio simultaneo, chiusura contest e blocco sponsor; configurare GitHub/Streamlit e provare l'URL pubblico. La V1 si ferma qui, prima del deployment, come richiesto.
