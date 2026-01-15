# Atomo

Un clone dell'editor di testo **GNU nano** scritto in Python, utilizzando la libreria `curses` per l'interfaccia terminale.

## Descrizione

Atomo è un editor di testo leggero per terminale che replica le funzionalità principali di nano. Ideale per l'editing rapido di file di configurazione, script e documenti di testo direttamente dalla riga di comando.

## Caratteristiche

- Interfaccia familiare in stile nano
- Supporto completo per la navigazione con tastiera
- Ricerca testuale nel documento
- Taglia/incolla righe
- Indicatore di file modificato
- Barre di stato e aiuto integrate
- Supporto per file UTF-8
- Scroll orizzontale e verticale automatico

## Requisiti

- Python 3.x
- Libreria `curses` (inclusa di default su Linux/macOS)

## Installazione

```bash
git clone https://github.com/tuousername/atomo.git
cd atomo
```

## Uso

```bash
# Aprire un file esistente
python atomo.py nomefile.txt

# Creare un nuovo file
python atomo.py nuovofile.txt

# Avviare senza file
python atomo.py
```

## Scorciatoie da Tastiera

| Comando | Descrizione |
|---------|-------------|
| `Ctrl+X` | Esci |
| `Ctrl+O` | Salva |
| `Ctrl+W` | Cerca |
| `Ctrl+K` | Taglia riga |
| `Ctrl+U` | Incolla riga |
| `Ctrl+G` | Mostra aiuto |
| `Ctrl+A` | Vai a inizio riga |
| `Ctrl+E` | Vai a fine riga |
| `Page Up/Down` | Scorri pagina |
| `Home/End` | Inizio/fine riga |
| `Tab` | Inserisce 4 spazi |

## Screenshot

```
┌─────────────────────────────────────────────────────┐
│  Atomo - nomefile.txt                               │
├─────────────────────────────────────────────────────┤
│ Il tuo testo qui...                                 │
│                                                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│ ^X Esci  ^O Salva  ^W Cerca  ^K Taglia  ^U Incolla  │
└─────────────────────────────────────────────────────┘
```

## Struttura del Codice

Il progetto è organizzato in una singola classe `AtomoEditor` che gestisce:

- **Stato dell'editor**: contenuto del file, posizione cursore, flag di modifica
- **Rendering**: disegno dell'interfaccia con barre di stato e titolo
- **Input**: gestione di tutti i tasti e le scorciatoie
- **File I/O**: caricamento e salvataggio dei file

## Licenza

Questo progetto è rilasciato sotto licenza [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.html).

## Autore

EdeFede

---

*Progetto educativo ispirato a GNU nano*
