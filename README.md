# Idee poco intelligenti e molto artificiali

Archivio dei post e dei caroselli LinkedIn di Andrea Marcellusi sul mercato farmaceutico italiano, con fonti, dati, ripensamenti e podcast.

Sito: https://ideeartificiali.it

## Come è fatto

- `content/idee/NN-slug.md`: una scheda per idea (metadati in testa, testo del post sotto).
- `content/site.yml`: titolo, temi, frasi del nastro, prompt della copertina.
- `content/ripensamenti.md`, `numeri.md`, `voci.md`, `istruzioni.md`: le altre sezioni.
- `assets/caroselli/<slug>.pdf` e `assets/caroselli/<slug>/p-*.jpg`: i caroselli e le loro pagine.
- `assets/immagini/`: le infografiche singole.
- `templates/`: HTML e CSS.
- `build.py`: genera il sito in `docs/`, che GitHub Pages pubblica così com'è.

## Aggiornare

1. Aggiungere o modificare un file in `content/` (e gli allegati in `assets/`).
2. Eseguire `python build.py` (richiede `pyyaml`, `markdown`, `jinja2`).
3. Caricare le modifiche su GitHub: il sito si aggiorna in un paio di minuti.

Il passo 2 può essere automatizzato con GitHub Actions; per ora si fa a mano.

## Licenza

Contenuti CC BY 4.0 salvo diversa indicazione. Codice del generatore: MIT.
