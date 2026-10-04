# Aggiornamento prima dell'invito ai colleghi

## Pubblicare il codice aggiornato

La cartella originale del progetto e la copia clonata con GitHub Desktop sono due cartelle diverse. Le modifiche devono essere presenti nella cartella `Pic_calcetto` mostrata da **Repository → Show in Explorer**, poi salvate con **Commit to main** e inviate con **Push origin**. Streamlit aggiorna il sito da GitHub.

Non copiare `.env`, `.streamlit/secrets.toml`, `runtime` o cartelle cache. Mantieni l'esclusione `assets/kits/1. MAGLIETTE/` nel `.gitignore` della copia GitHub.

## Attivare il reset delle prove

1. In Supabase seleziona **Calcetto FAVERO** nella barra superiore.
2. Apri **SQL Editor**: l'icona `>_` a sinistra, sotto Table Editor.
3. Crea una nuova query con **New query** / `+`.
4. Apri `sql/migrations/001_admin_reset_votes.sql` con Blocco note, copia tutto e incollalo nella query.
5. Premi **Run**. Il risultato deve indicare successo. Questa query aggiunge una funzione; non elimina voti e non cambia le tabelle.
6. Non eseguire nuovamente `sql/schema.sql`: è lo schema iniziale, non la migrazione.

Nel sito apri **admin**, accedi e scegli **Reset prove**. Seleziona soltanto i nominativi delle prove, scrivi `RESET`, inserisci la tua password Admin e premi **Resetta i voti selezionati**. I partecipanti selezionati possono votare di nuovo; gli altri voti restano intatti. Non c'è un reset indiscriminato di tutti i voti. Il reset è definitivo: prima puoi conservare l'export CSV. Se l'amico ha già aperto il sito, chiedigli di ricaricarlo dopo il reset.

## Accesso Admin

La pagina è accessibile soltanto dopo il login: nessuna lettura o scrittura Admin viene eseguita prima dell'autenticazione. La protezione identifica chi conosce username e password, non una persona fisica. Non condividere la password e usane una personale non riutilizzata. L'hash nei Secrets è la rappresentazione verificabile della password, non la password da digitare.

Per cambiare password, esegui `python scripts/generate_password_hash.py` dalla cartella del progetto. Aggiorna `ADMIN_PASSWORD_HASH` nei Secrets di Streamlit (**My apps → ⋮ → Settings → Secrets → Save**). Dopo il cambio le sessioni Admin precedenti richiedono un nuovo login. Il login dura un'ora e dispone di logout. Mantieni allineati i file privati locali se usi anche l'app sul computer.

## Voto e preview

Ordine: **Nome + logo → Sponsor → Maglia → Riepilogo e conferma**. Tutte le tre maglie disponibili mostrano subito lo stemma e il nome dello sponsor scelto come scritta sul petto. La vista di dettaglio mostra entrambi; le altre viste sono le foto Macron originali. Non sono stati inventati loghi sponsor, né rigenerate le maglie. L'overlay è una preview indicativa della stampa; posizione e resa di produzione vanno confermate col fornitore.

Il submit conserva i campi attuali: `team_name_choice = crest_choice = nome scelto`, `kit_choice = maglia scelta`, `sponsor_id = sponsor scelto`. La regola un voto per partecipante rimane attiva; l'Admin può riabilitare soltanto i partecipanti selezionati con il reset esplicito.

## Risultati

La prima scheda Admin **Risultati** mostra totale, voti mancanti e completamento, anche per squadra. Le tre classifiche **Nome e logo**, **Sponsor**, **Maglia** riportano voti, percentuali, scelta in testa ed eventuali pari merito. Il dettaglio filtrabile per squadra riporta nominativo, scelte e data UTC. L'export CSV rimane disponibile nella scheda **Export**.

## Verifica prima della distribuzione

Accedi al link pubblico in una finestra privata: l'Admin deve chiedere la password. Crea un partecipante `TEST AMICO`, verifica con lui il nuovo ordine, le preview e un invio reale. Controlla il voto nella scheda Risultati, poi usa Reset prove soltanto per `TEST AMICO`. Non raccogliere voti definitivi finché la prova pubblica non è completata.
