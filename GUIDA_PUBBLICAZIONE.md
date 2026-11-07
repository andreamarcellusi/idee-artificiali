# Mettere online il sito, passo per passo

Tempo: 15 minuti. Serve solo il browser e un programma gratuito (GitHub Desktop).

## A. Installare GitHub Desktop (una volta sola)

1. Vai su https://desktop.github.com e clicca **Download for Windows**. Installa.
2. All'apertura clicca **Sign in to GitHub.com** e accedi con il tuo account (si apre il browser, conferma).
3. Alla schermata "Configure Git" lascia nome ed email proposti e clicca **Finish**.

## B. Scaricare il repository sul PC

1. In GitHub Desktop: **File → Clone repository**.
2. Nella scheda **GitHub.com** scegli `andreamarcellusi/idee-artificiali`.
3. In "Local path" lascia la cartella proposta (di solito `Documents\GitHub`). Clicca **Clone**.

Ora sul PC esiste la cartella `Documents\GitHub\idee-artificiali` con dentro solo il README.

## C. Copiare il sito dentro quella cartella

1. Apri lo zip `idee-artificiali.zip` e dentro trovi una cartella `idee-artificiali`.
2. Seleziona **tutto il contenuto** di quella cartella (build.py, content, assets, templates, docs, README.md...).
3. Incollalo dentro `Documents\GitHub\idee-artificiali`. Se chiede di sostituire README.md, conferma.

## D. Pubblicare

1. Torna in GitHub Desktop: a sinistra vedi l'elenco dei file nuovi (qualche centinaio).
2. In basso a sinistra, nella casella "Summary", scrivi: `Prima versione del sito`.
3. Clicca **Commit to main**.
4. In alto clicca **Push origin** (o **Publish branch**). Aspetta che finisca la barra.

## E. Attivare la pubblicazione (una volta sola)

1. Nel browser vai su https://github.com/andreamarcellusi/idee-artificiali/settings/pages
2. In **Build and deployment → Source** lascia **Deploy from a branch**.
3. In **Branch** scegli `main` e, nel menu accanto, **/docs** (non /root). Clicca **Save**.
4. Dopo 1-3 minuti ricarica la pagina: compare "Your site is live at https://andreamarcellusi.github.io/idee-artificiali/". Aprilo.

## Da qui in poi: aggiornare il sito

Ogni volta che ti consegno un aggiornamento (nuova scheda, testi importati, dataset):

1. Copia i file nuovi dentro `Documents\GitHub\idee-artificiali`, sovrascrivendo.
2. GitHub Desktop → scrivi due parole in Summary → **Commit to main** → **Push origin**.

Il sito si aggiorna da solo in un paio di minuti. Non serve altro.

## Se qualcosa non torna

- "Push" chiede di nuovo le credenziali: accedi con lo stesso account del browser.
- Il sito mostra solo il README: nelle impostazioni Pages controlla di aver scelto **/docs** e non /root.
- Il sito è online ma senza immagini: aspetta due minuti e ricarica con Ctrl+F5.
