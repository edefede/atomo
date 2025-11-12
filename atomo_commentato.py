#!/usr/bin/env python3
"""
Atomo - Clone dell'editor di testo nano in Python
Uso: python atomo.py [nome_file]

Questo è un editor di testo basato su terminale che imita le funzionalità
di base dell'editor GNU nano, utilizzando la libreria curses per la gestione
dell'interfaccia testuale.
"""

import curses  # Libreria per gestire l'interfaccia testuale nel terminale
import sys     # Per accedere agli argomenti della riga di comando
import os      # Per operazioni sui file
from typing import List, Optional, Tuple  # Type hints per maggiore chiarezza


class AtomoEditor:
    """
    Classe principale dell'editor che gestisce l'interfaccia di editing del testo.

    Questa classe contiene tutto lo stato dell'editor: il contenuto del file,
    la posizione del cursore, lo stato di modifica, e gestisce il rendering
    e l'input dell'utente.
    """

    def __init__(self, stdscr, filename: Optional[str] = None):
        """
        Inizializza l'editor.

        Args:
            stdscr: Lo schermo curses standard fornito da curses.wrapper()
            filename: Nome del file opzionale da caricare all'avvio

        Questa funzione imposta tutti i parametri iniziali dell'editor:
        - Configura i colori per l'interfaccia
        - Inizializza le variabili di stato (cursore, scroll, modifiche)
        - Carica il file se specificato
        """
        self.stdscr = stdscr              # Riferimento allo schermo curses
        self.filename = filename          # Nome del file corrente
        self.lines: List[str] = []        # Lista delle righe di testo
        self.cursor_y = 0                 # Posizione Y del cursore (riga)
        self.cursor_x = 0                 # Posizione X del cursore (colonna)
        self.offset_y = 0                 # Offset dello scroll verticale
        self.offset_x = 0                 # Offset dello scroll orizzontale
        self.modified = False             # Flag che indica se il file è stato modificato
        self.message = ""                 # Messaggio da mostrare all'utente
        self.message_type = "info"        # Tipo di messaggio: info, error, success

        # Inizializza i colori per l'interfaccia
        curses.start_color()              # Abilita il supporto colori
        curses.use_default_colors()       # Usa i colori predefiniti del terminale

        # Definisce coppie di colori (foreground, background):
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Barra di stato
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Barra del titolo
        curses.init_pair(3, curses.COLOR_RED, -1)                    # Messaggi di errore
        curses.init_pair(4, curses.COLOR_GREEN, -1)                  # Messaggi di successo

        # Configurazione di curses
        curses.curs_set(1)                # Mostra il cursore (1=visibile, 0=invisibile)
        self.stdscr.keypad(True)          # Abilita le chiavi speciali (frecce, F1-F12, ecc.)

        # Carica il file se specificato
        if filename:
            self.load_file(filename)
        else:
            self.lines = [""]             # Inizia con una riga vuota

    def load_file(self, filename: str) -> bool:
        """
        Carica un file nell'editor.

        Args:
            filename: Percorso del file da caricare

        Returns:
            True se il caricamento è riuscito, False in caso di errore

        Questa funzione:
        - Controlla se il file esiste
        - Se esiste, legge tutte le righe
        - Se non esiste, inizializza un nuovo buffer vuoto
        - Gestisce gli errori di lettura e mostra messaggi appropriati
        """
        try:
            if os.path.exists(filename):
                # Il file esiste, lo legge
                with open(filename, 'r', encoding='utf-8') as f:
                    self.lines = f.read().splitlines()  # Legge e divide in righe
                    if not self.lines:
                        self.lines = [""]  # Assicura almeno una riga vuota
                self.message = f'Lette {len(self.lines)} righe da {filename}'
                self.message_type = "success"
            else:
                # Il file non esiste, crea un nuovo buffer
                self.lines = [""]
                self.message = f'Nuovo File: {filename}'
                self.message_type = "info"

            self.filename = filename
            self.modified = False  # Il file appena caricato non è modificato
            return True
        except Exception as e:
            # Gestisce errori di lettura (permessi, encoding, ecc.)
            self.message = f'Errore leggendo {filename}: {str(e)}'
            self.message_type = "error"
            self.lines = [""]
            return False

    def save_file(self, filename: Optional[str] = None) -> bool:
        """
        Salva il buffer corrente su file.

        Args:
            filename: Nome del file dove salvare (opzionale, usa quello corrente se None)

        Returns:
            True se il salvataggio è riuscito, False altrimenti

        Questa funzione:
        - Scrive tutte le righe nel file
        - Aggiunge una newline finale se l'ultima riga ha contenuto
        - Aggiorna lo stato di modifica
        - Gestisce eventuali errori di scrittura
        """
        if filename:
            self.filename = filename  # Aggiorna il nome del file se fornito

        if not self.filename:
            return False  # Non può salvare senza un nome file

        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                # Unisce tutte le righe con newline
                f.write('\n'.join(self.lines))
                # Aggiunge newline finale se l'ultima riga ha contenuto
                if self.lines and self.lines[-1]:
                    f.write('\n')

            self.modified = False  # Resetta il flag di modifica
            self.message = f'Scritte {len(self.lines)} righe in {self.filename}'
            self.message_type = "success"
            return True
        except Exception as e:
            # Gestisce errori di scrittura (permessi, disco pieno, ecc.)
            self.message = f'Errore scrivendo {self.filename}: {str(e)}'
            self.message_type = "error"
            return False

    def get_dimensions(self) -> Tuple[int, int]:
        """
        Ottiene le dimensioni utilizzabili dello schermo (escludendo le barre).

        Returns:
            Tupla (altezza, larghezza) dell'area di editing

        Questa funzione calcola lo spazio disponibile per il testo sottraendo
        lo spazio occupato dalle barre del titolo, stato e aiuto:
        - 1 riga per la barra del titolo
        - 1 riga per i messaggi
        - 2 righe per le barre di stato e aiuto
        Totale: 4 righe riservate
        """
        max_y, max_x = self.stdscr.getmaxyx()  # Ottiene le dimensioni totali dello schermo
        # Riserva 2 righe per il titolo e 2 righe per stato/aiuto
        return max_y - 4, max_x

    def safe_addstr(self, y, x, text, attr=0):
        """
        Aggiunge in modo sicuro una stringa allo schermo con gestione degli errori.

        Args:
            y: Coordinata Y dove scrivere
            x: Coordinata X dove scrivere
            text: Testo da scrivere
            attr: Attributi opzionali (colore, grassetto, ecc.)

        Questa funzione protegge da errori curses che si verificano quando si
        tenta di scrivere oltre i bordi dello schermo. Tronca il testo se necessario
        e ignora gli errori curses.
        """
        max_y, max_x = self.stdscr.getmaxyx()

        # Controlla se la posizione è fuori schermo
        if y >= max_y or x >= max_x:
            return

        # Calcola la lunghezza massima che può essere scritta
        max_len = max_x - x - 1
        if max_len <= 0:
            return

        # Tronca il testo per adattarlo allo spazio disponibile
        text = str(text)[:max_len]

        try:
            # Scrive il testo con o senza attributi
            if attr:
                self.stdscr.addstr(y, x, text, attr)
            else:
                self.stdscr.addstr(y, x, text)
        except curses.error:
            # Ignora gli errori curses (di solito quando si scrive sul bordo)
            pass

    def draw_title_bar(self):
        """
        Disegna la barra del titolo in alto.

        Mostra:
        - Il nome dell'editor ("GNU nano clone - Atomo")
        - Il nome del file corrente al centro
        - Un asterisco (*) se il file è stato modificato

        La barra usa uno sfondo blu con testo bianco e grassetto.
        """
        max_y, max_x = self.stdscr.getmaxyx()
        title = "  GNU nano clone - Atomo"
        filename_display = self.filename if self.filename else "[New Buffer]"

        # Indicatore di modifica (asterisco se il file è stato modificato)
        mod_indicator = " *" if self.modified else ""

        # Attiva colore blu e grassetto per la barra del titolo
        self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)

        # Riempie l'intera riga con spazi (sfondo)
        self.safe_addstr(0, 0, " " * (max_x - 1))
        # Scrive il titolo a sinistra
        self.safe_addstr(0, 0, title)

        # Mostra il nome del file centrato
        filename_str = f" File: {filename_display}{mod_indicator} "
        if len(filename_str) < max_x - len(title):
            x_pos = (max_x - len(filename_str)) // 2  # Calcola posizione centrale
            self.safe_addstr(0, x_pos, filename_str)

        # Disattiva gli attributi
        self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)

    def draw_status_bar(self):
        """
        Disegna la barra di stato in basso.

        Mostra informazioni sulla posizione corrente:
        - Numero di riga corrente e totale righe
        - Numero di colonna corrente

        Es: "Line 5/42  Col 12"

        La barra usa uno sfondo bianco con testo nero.
        """
        max_y, max_x = self.stdscr.getmaxyx()

        # Crea la stringa di stato con informazioni sulla posizione
        # +1 perché per l'utente le righe/colonne partono da 1, non da 0
        status_left = f" Line {self.cursor_y + 1}/{len(self.lines)}  Col {self.cursor_x + 1} "

        # Attiva lo stile della barra di stato
        self.stdscr.attron(curses.color_pair(1))
        # Scrive la barra alla penultima riga dello schermo
        self.safe_addstr(max_y - 2, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 2, 0, status_left)
        self.stdscr.attroff(curses.color_pair(1))

    def draw_help_bar(self):
        """
        Disegna la barra di aiuto con le scorciatoie da tastiera.

        Mostra le principali scorciatoie disponibili:
        - ^X Exit: Esci dall'editor
        - ^O Save: Salva il file
        - ^W Where Is: Cerca nel testo
        - ^K Cut: Taglia la riga
        - ^U Paste: Incolla la riga
        - ^G Help: Mostra la schermata di aiuto

        Il simbolo ^ indica il tasto Ctrl.
        """
        max_y, max_x = self.stdscr.getmaxyx()

        # Lista delle scorciatoie da visualizzare
        shortcuts = [
            ("^X", "Exit"), ("^O", "Save"), ("^W", "Where Is"),
            ("^K", "Cut"), ("^U", "Paste"), ("^G", "Help")
        ]

        # Crea la stringa con tutte le scorciatoie
        help_text = "  "
        for key, desc in shortcuts:
            help_text += f"{key} {desc}   "

        # Disegna la barra all'ultima riga dello schermo
        self.stdscr.attron(curses.color_pair(1))
        self.safe_addstr(max_y - 1, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 1, 0, help_text)
        self.stdscr.attroff(curses.color_pair(1))

    def draw_message(self):
        """
        Disegna la riga dei messaggi se presente.

        Mostra messaggi all'utente con colori diversi a seconda del tipo:
        - Rosso per errori
        - Verde per successi
        - Normale per informazioni

        I messaggi appaiono nella riga sopra le barre di stato/aiuto.
        """
        if self.message:
            max_y, max_x = self.stdscr.getmaxyx()

            # Seleziona il colore in base al tipo di messaggio
            color = curses.color_pair(3) if self.message_type == "error" else \
                    curses.color_pair(4) if self.message_type == "success" else 0

            # Pulisce la riga
            self.safe_addstr(max_y - 3, 0, " " * (max_x - 1))
            # Scrive il messaggio con il colore appropriato e grassetto
            self.stdscr.attron(color | curses.A_BOLD)
            self.safe_addstr(max_y - 3, 0, f" {self.message}")
            self.stdscr.attroff(color | curses.A_BOLD)

    def draw_buffer(self):
        """
        Disegna il contenuto del buffer di testo.

        Questa funzione:
        - Mostra le righe di testo visibili nell'area di editing
        - Applica lo scroll verticale e orizzontale
        - Gestisce righe vuote e righe più lunghe dello schermo

        L'area di editing inizia dalla riga 1 (dopo la barra del titolo) e
        si estende fino alla riga dei messaggi.
        """
        height, width = self.get_dimensions()

        # Itera su tutte le righe visibili sullo schermo
        for screen_y in range(height):
            # Calcola quale riga del buffer corrisponde a questa riga dello schermo
            buffer_y = screen_y + self.offset_y

            # Pulisce la riga sullo schermo
            self.safe_addstr(screen_y + 1, 0, " " * width)

            # Se c'è una riga da mostrare nel buffer
            if buffer_y < len(self.lines):
                line = self.lines[buffer_y]
                # Applica lo scroll orizzontale: mostra solo la parte visibile
                visible_line = line[self.offset_x:self.offset_x + width]
                # Disegna la riga (+1 per saltare la barra del titolo)
                self.safe_addstr(screen_y + 1, 0, visible_line)

    def draw(self):
        """
        Disegna l'intera interfaccia dell'editor.

        Questa è la funzione principale di rendering che:
        1. Pulisce lo schermo
        2. Disegna tutti i componenti in ordine:
           - Barra del titolo
           - Buffer di testo
           - Messaggi
           - Barra di stato
           - Barra di aiuto
        3. Posiziona il cursore nella posizione corretta
        4. Aggiorna lo schermo

        Viene chiamata ad ogni iterazione del ciclo principale.
        """
        self.stdscr.clear()           # Pulisce lo schermo
        self.draw_title_bar()         # Disegna il titolo
        self.draw_buffer()            # Disegna il testo
        self.draw_message()           # Disegna i messaggi
        self.draw_status_bar()        # Disegna lo stato
        self.draw_help_bar()          # Disegna l'aiuto

        # Calcola la posizione del cursore sullo schermo
        # Tiene conto dello scroll e della barra del titolo (+1)
        screen_y = self.cursor_y - self.offset_y + 1
        screen_x = self.cursor_x - self.offset_x
        height, width = self.get_dimensions()

        # Posiziona il cursore solo se è visibile nell'area di editing
        if 0 <= screen_y < height + 1 and 0 <= screen_x < width:
            self.stdscr.move(screen_y, screen_x)

        self.stdscr.refresh()         # Aggiorna lo schermo fisico

    def adjust_scroll(self):
        """
        Regola gli offset di scroll per mantenere il cursore visibile.

        Questa funzione si assicura che il cursore sia sempre visibile sullo schermo:
        - Se il cursore va sopra l'area visibile, scrolla verso l'alto
        - Se il cursore va sotto l'area visibile, scrolla verso il basso
        - Se il cursore va a sinistra dell'area visibile, scrolla a sinistra
        - Se il cursore va a destra dell'area visibile, scrolla a destra

        Viene chiamata dopo ogni movimento del cursore.
        """
        height, width = self.get_dimensions()

        # Scroll verticale
        if self.cursor_y < self.offset_y:
            # Cursore sopra l'area visibile: scrolla verso l'alto
            self.offset_y = self.cursor_y
        elif self.cursor_y >= self.offset_y + height:
            # Cursore sotto l'area visibile: scrolla verso il basso
            self.offset_y = self.cursor_y - height + 1

        # Scroll orizzontale
        if self.cursor_x < self.offset_x:
            # Cursore a sinistra dell'area visibile: scrolla a sinistra
            self.offset_x = self.cursor_x
        elif self.cursor_x >= self.offset_x + width:
            # Cursore a destra dell'area visibile: scrolla a destra
            self.offset_x = self.cursor_x - width + 1

    def move_cursor(self, dy: int, dx: int):
        """
        Muove il cursore di un certo offset.

        Args:
            dy: Spostamento verticale (positivo=giù, negativo=su)
            dx: Spostamento orizzontale (positivo=destra, negativo=sinistra)

        Questa funzione:
        - Calcola la nuova posizione del cursore
        - Si assicura che rimanga nei limiti validi
        - Regola la posizione X se la nuova riga è più corta
        - Aggiorna lo scroll se necessario
        """
        # Calcola la nuova posizione Y
        new_y = self.cursor_y + dy
        # Limita Y tra 0 e l'ultima riga
        new_y = max(0, min(new_y, len(self.lines) - 1))

        self.cursor_y = new_y

        # Calcola la nuova posizione X
        new_x = self.cursor_x + dx
        # Limita X tra 0 e la lunghezza della riga corrente
        new_x = max(0, min(new_x, len(self.lines[self.cursor_y])))

        self.cursor_x = new_x

        # Aggiorna lo scroll per mantenere il cursore visibile
        self.adjust_scroll()

    def insert_char(self, char: str):
        """
        Inserisce uno o più caratteri alla posizione del cursore.

        Args:
            char: Carattere o stringa da inserire (può essere anche tab = 4 spazi)

        Questa funzione:
        - Inserisce il carattere nella riga corrente
        - Aggiorna la posizione del cursore
        - Marca il file come modificato
        - Gestisce lo scroll orizzontale
        """
        # Ottiene la riga corrente
        line = self.lines[self.cursor_y]
        # Inserisce il carattere alla posizione del cursore
        # line[:self.cursor_x] = parte prima del cursore
        # char = carattere da inserire
        # line[self.cursor_x:] = parte dopo il cursore
        self.lines[self.cursor_y] = line[:self.cursor_x] + char + line[self.cursor_x:]

        # Sposta il cursore dopo il carattere inserito
        self.cursor_x += len(char)

        # Marca il file come modificato
        self.modified = True

        # Aggiorna lo scroll
        self.adjust_scroll()

    def delete_char(self):
        """
        Cancella il carattere sotto il cursore (tasto Delete).

        Questa funzione:
        - Se c'è un carattere dopo il cursore, lo cancella
        - Se il cursore è alla fine della riga, unisce con la riga successiva
        - Marca il file come modificato
        """
        line = self.lines[self.cursor_y]

        # Se il cursore non è alla fine della riga
        if self.cursor_x < len(line):
            # Rimuove il carattere sotto il cursore
            self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x + 1:]
            self.modified = True
        # Se il cursore è alla fine della riga e c'è una riga successiva
        elif self.cursor_y < len(self.lines) - 1:
            # Unisce la riga corrente con quella successiva
            next_line = self.lines.pop(self.cursor_y + 1)
            self.lines[self.cursor_y] += next_line
            self.modified = True

    def backspace(self):
        """
        Cancella il carattere prima del cursore (tasto Backspace).

        Questa funzione:
        - Se il cursore non è all'inizio della riga, cancella il carattere precedente
        - Se il cursore è all'inizio della riga, unisce con la riga precedente
        - Aggiorna la posizione del cursore
        - Marca il file come modificato
        """
        # Se il cursore non è all'inizio della riga
        if self.cursor_x > 0:
            line = self.lines[self.cursor_y]
            # Rimuove il carattere prima del cursore
            self.lines[self.cursor_y] = line[:self.cursor_x - 1] + line[self.cursor_x:]
            # Sposta il cursore indietro
            self.cursor_x -= 1
            self.modified = True
            self.adjust_scroll()
        # Se il cursore è all'inizio ma non è la prima riga
        elif self.cursor_y > 0:
            # Salva la riga corrente
            current_line = self.lines[self.cursor_y]
            # Rimuove la riga corrente
            self.lines.pop(self.cursor_y)
            # Sposta il cursore alla fine della riga precedente
            self.cursor_y -= 1
            self.cursor_x = len(self.lines[self.cursor_y])
            # Appende il contenuto della riga rimossa alla riga precedente
            self.lines[self.cursor_y] += current_line
            self.modified = True
            self.adjust_scroll()

    def insert_newline(self):
        """
        Inserisce una nuova riga alla posizione del cursore (tasto Enter).

        Questa funzione:
        - Divide la riga corrente in due parti al cursore
        - Crea una nuova riga con la parte dopo il cursore
        - Sposta il cursore all'inizio della nuova riga
        - Marca il file come modificato
        """
        line = self.lines[self.cursor_y]
        # Parte prima del cursore rimane sulla riga corrente
        self.lines[self.cursor_y] = line[:self.cursor_x]
        # Parte dopo il cursore va sulla nuova riga
        new_line = line[self.cursor_x:]
        # Inserisce la nuova riga dopo quella corrente
        self.lines.insert(self.cursor_y + 1, new_line)

        # Sposta il cursore all'inizio della nuova riga
        self.cursor_y += 1
        self.cursor_x = 0

        self.modified = True
        self.adjust_scroll()

    def prompt_input(self, prompt: str) -> Optional[str]:
        """
        Mostra un prompt e ottiene input dall'utente.

        Args:
            prompt: Testo del prompt da mostrare

        Returns:
            Stringa inserita dall'utente, o None se annullato (ESC)

        Questa funzione:
        - Mostra il prompt nella riga dei messaggi
        - Permette all'utente di digitare una risposta
        - Gestisce backspace per correzioni
        - Permette di annullare con ESC
        """
        max_y, max_x = self.stdscr.getmaxyx()
        input_str = ""

        while True:
            # Pulisce e mostra il prompt con l'input corrente
            self.stdscr.attron(curses.color_pair(1))
            self.safe_addstr(max_y - 3, 0, " " * (max_x - 1))
            self.safe_addstr(max_y - 3, 0, f"{prompt}{input_str}")
            self.stdscr.attroff(curses.color_pair(1))
            self.stdscr.refresh()

            key = self.stdscr.getch()

            # Enter: conferma input
            if key in [curses.KEY_ENTER, 10, 13]:
                return input_str
            # ESC: annulla
            elif key == 27:
                return None
            # Backspace: cancella ultimo carattere
            elif key in [curses.KEY_BACKSPACE, 127, 8]:
                input_str = input_str[:-1]
            # Caratteri stampabili: aggiunge all'input
            elif 32 <= key <= 126:
                input_str += chr(key)

    def prompt_save_filename(self) -> Optional[str]:
        """
        Chiede all'utente il nome del file per salvare.

        Returns:
            Nome del file inserito dall'utente, o None se annullato

        Se esiste già un nome file, viene proposto come predefinito.
        """
        prompt = f"File Name to Write: "
        # Se esiste già un filename, lo usa come predefinito
        if self.filename:
            return self.filename

        # Altrimenti chiede all'utente
        filename = self.prompt_input(prompt)
        return filename if filename else None

    def prompt_search(self) -> Optional[str]:
        """
        Chiede all'utente il testo da cercare.

        Returns:
            Stringa di ricerca, o None se annullato
        """
        return self.prompt_input("Search: ")

    def search(self, query: str):
        """
        Cerca una stringa nel testo e sposta il cursore alla prima occorrenza.

        Args:
            query: Stringa da cercare

        Questa funzione:
        - Cerca dalla posizione corrente del cursore in avanti
        - Wrappa all'inizio del file se non trova nulla
        - Sposta il cursore alla prima occorrenza trovata
        - Mostra un messaggio se non trova nulla

        La ricerca è case-sensitive e lineare.
        """
        if not query:
            return

        # Salva la posizione iniziale
        start_y = self.cursor_y
        start_x = self.cursor_x + 1  # Cerca dal carattere successivo

        # Cerca prima nella riga corrente (dalla posizione del cursore)
        pos = self.lines[start_y][start_x:].find(query)
        if pos != -1:
            # Trovato nella riga corrente
            self.cursor_x = start_x + pos
            self.message = f"Found '{query}'"
            self.message_type = "success"
            self.adjust_scroll()
            return

        # Cerca nelle righe successive
        for y in range(start_y + 1, len(self.lines)):
            pos = self.lines[y].find(query)
            if pos != -1:
                # Trovato in una riga successiva
                self.cursor_y = y
                self.cursor_x = pos
                self.message = f"Found '{query}'"
                self.message_type = "success"
                self.adjust_scroll()
                return

        # Wrappa e cerca dall'inizio fino alla posizione iniziale
        for y in range(0, start_y):
            pos = self.lines[y].find(query)
            if pos != -1:
                # Trovato dall'inizio (wrapped)
                self.cursor_y = y
                self.cursor_x = pos
                self.message = f"Found '{query}' (wrapped)"
                self.message_type = "success"
                self.adjust_scroll()
                return

        # Non trovato
        self.message = f"'{query}' not found"
        self.message_type = "error"

    def show_help(self):
        """
        Mostra la schermata di aiuto con tutti i comandi disponibili.

        Questa funzione:
        - Pulisce lo schermo
        - Mostra un elenco completo dei comandi
        - Aspetta che l'utente prema un tasto per continuare
        - Poi torna alla normale visualizzazione dell'editor
        """
        max_y, max_x = self.stdscr.getmaxyx()

        # Testo di aiuto con tutti i comandi
        help_text = [
            "Atomo Help - A nano clone",
            "",
            "Main commands:",
            "  Ctrl+X  Exit (prompts to save if modified)",
            "  Ctrl+O  Save file (Write Out)",
            "  Ctrl+W  Search (Where Is)",
            "  Ctrl+K  Cut line",
            "  Ctrl+U  Paste line",
            "  Ctrl+G  Show this help",
            "",
            "Navigation:",
            "  Arrow Keys  Move cursor",
            "  Home/Ctrl+A Beginning of line",
            "  End/Ctrl+E  End of line",
            "  Page Up/Down Scroll page",
            "",
            "Editing:",
            "  Enter      Insert new line",
            "  Backspace  Delete character before cursor",
            "  Delete     Delete character at cursor",
            "",
            "Press any key to continue..."
        ]

        # Pulisce lo schermo e mostra il testo di aiuto
        self.stdscr.clear()
        for i, line in enumerate(help_text):
            if i < max_y - 1:  # Non scrivere oltre i limiti dello schermo
                self.safe_addstr(i, 2, line)

        self.stdscr.refresh()
        self.stdscr.getch()  # Aspetta un tasto qualsiasi

    def confirm_exit(self) -> bool:
        """
        Chiede conferma all'utente prima di uscire se ci sono modifiche non salvate.

        Returns:
            True se l'utente vuole uscire, False se annulla

        Questa funzione:
        - Se non ci sono modifiche, ritorna True immediatamente
        - Altrimenti chiede: Salvare? (Y/N/C per annullare)
        - Y: Salva e esce
        - N: Esce senza salvare
        - C/ESC: Annulla e torna all'editor
        """
        if not self.modified:
            # Nessuna modifica, può uscire direttamente
            return True

        max_y, max_x = self.stdscr.getmaxyx()
        prompt = "Save modified buffer? (Y/N/C for cancel) "

        # Mostra il prompt
        self.stdscr.attron(curses.color_pair(1))
        self.safe_addstr(max_y - 3, 0, " " * (max_x - 1))
        self.safe_addstr(max_y - 3, 0, prompt)
        self.stdscr.attroff(curses.color_pair(1))
        self.stdscr.refresh()

        # Loop finché non riceve una risposta valida
        while True:
            key = self.stdscr.getch()
            if key in [ord('y'), ord('Y')]:
                # Salva e esci
                filename = self.prompt_save_filename()
                if filename and self.save_file(filename):
                    return True
                return False
            elif key in [ord('n'), ord('N')]:
                # Esci senza salvare
                return True
            elif key in [ord('c'), ord('C'), 27]:  # 27 è ESC
                # Annulla
                return False

    def run(self):
        """
        Loop principale dell'editor.

        Questa è la funzione principale che:
        1. Disegna l'interfaccia
        2. Aspetta input dall'utente
        3. Processa l'input (movimento cursore, inserimento testo, comandi)
        4. Aggiorna lo stato
        5. Ripete fino all'uscita

        Gestisce tutti i tasti e le scorciatoie:
        - Ctrl+X: Esci
        - Ctrl+O: Salva
        - Ctrl+W: Cerca
        - Ctrl+K: Taglia riga
        - Ctrl+U: Incolla riga
        - Ctrl+G: Aiuto
        - Ctrl+A: Inizio riga
        - Ctrl+E: Fine riga
        - Frecce: Navigazione
        - Enter: Nuova riga
        - Backspace/Delete: Cancella
        - Tab: Inserisce 4 spazi
        - Caratteri stampabili: Inserisce il carattere
        """
        cut_buffer = ""  # Buffer per taglia/incolla

        while True:
            self.draw()  # Disegna l'interfaccia
            key = self.stdscr.getch()  # Aspetta input

            # Gestisce Ctrl+X (Esci)
            if key == 24:  # Ctrl+X = ASCII 24
                if self.confirm_exit():
                    break  # Esce dal loop e termina il programma

            # Gestisce Ctrl+O (Salva)
            elif key == 15:  # Ctrl+O = ASCII 15
                filename = self.prompt_save_filename()
                if filename:
                    self.save_file(filename)

            # Gestisce Ctrl+W (Cerca)
            elif key == 23:  # Ctrl+W = ASCII 23
                query = self.prompt_search()
                if query:
                    self.search(query)

            # Gestisce Ctrl+K (Taglia riga)
            elif key == 11:  # Ctrl+K = ASCII 11
                if self.lines:
                    # Salva la riga corrente nel buffer di cut
                    cut_buffer = self.lines[self.cursor_y]
                    # Rimuove la riga
                    self.lines.pop(self.cursor_y)
                    # Assicura almeno una riga vuota
                    if not self.lines:
                        self.lines = [""]
                    # Regola la posizione del cursore
                    if self.cursor_y >= len(self.lines):
                        self.cursor_y = len(self.lines) - 1
                    self.cursor_x = 0
                    self.modified = True
                    self.message = "Cut line"
                    self.message_type = "info"

            # Gestisce Ctrl+U (Incolla)
            elif key == 21:  # Ctrl+U = ASCII 21
                if cut_buffer:
                    # Inserisce la riga dal buffer
                    self.lines.insert(self.cursor_y, cut_buffer)
                    self.modified = True
                    self.message = "Pasted line"
                    self.message_type = "info"

            # Gestisce Ctrl+G (Aiuto)
            elif key == 7:  # Ctrl+G = ASCII 7
                self.show_help()

            # Gestisce Ctrl+A (Inizio riga)
            elif key == 1:  # Ctrl+A = ASCII 1
                self.cursor_x = 0
                self.adjust_scroll()

            # Gestisce Ctrl+E (Fine riga)
            elif key == 5:  # Ctrl+E = ASCII 5
                self.cursor_x = len(self.lines[self.cursor_y])
                self.adjust_scroll()

            # Tasti di navigazione
            elif key == curses.KEY_UP:
                self.move_cursor(-1, 0)  # Su
            elif key == curses.KEY_DOWN:
                self.move_cursor(1, 0)   # Giù
            elif key == curses.KEY_LEFT:
                # Sinistra: se all'inizio della riga, va alla fine della precedente
                if self.cursor_x > 0:
                    self.move_cursor(0, -1)
                elif self.cursor_y > 0:
                    self.cursor_y -= 1
                    self.cursor_x = len(self.lines[self.cursor_y])
                    self.adjust_scroll()
            elif key == curses.KEY_RIGHT:
                # Destra: se alla fine della riga, va all'inizio della successiva
                if self.cursor_x < len(self.lines[self.cursor_y]):
                    self.move_cursor(0, 1)
                elif self.cursor_y < len(self.lines) - 1:
                    self.cursor_y += 1
                    self.cursor_x = 0
                    self.adjust_scroll()
            elif key == curses.KEY_HOME:
                self.cursor_x = 0
                self.adjust_scroll()
            elif key == curses.KEY_END:
                self.cursor_x = len(self.lines[self.cursor_y])
                self.adjust_scroll()
            elif key == curses.KEY_PPAGE:  # Page Up
                height, _ = self.get_dimensions()
                self.move_cursor(-height, 0)  # Salta una schermata su
            elif key == curses.KEY_NPAGE:  # Page Down
                height, _ = self.get_dimensions()
                self.move_cursor(height, 0)   # Salta una schermata giù

            # Gestisce Enter
            elif key in [curses.KEY_ENTER, 10, 13]:
                self.insert_newline()

            # Gestisce Backspace
            elif key in [curses.KEY_BACKSPACE, 127, 8]:
                self.backspace()

            # Gestisce Delete
            elif key == curses.KEY_DC:
                self.delete_char()

            # Gestisce Tab
            elif key == 9:
                self.insert_char('    ')  # Inserisce 4 spazi

            # Gestisce caratteri stampabili
            elif 32 <= key <= 126:
                # ASCII 32-126 sono i caratteri stampabili
                self.insert_char(chr(key))


def main(stdscr, filename: Optional[str] = None):
    """
    Punto di ingresso principale per l'applicazione curses.

    Args:
        stdscr: Schermo curses standard fornito da curses.wrapper()
        filename: Nome file opzionale da caricare

    Questa funzione:
    - Crea un'istanza di AtomoEditor
    - Avvia il loop principale dell'editor
    - Viene chiamata da curses.wrapper() che si occupa dell'inizializzazione
      e della pulizia di curses
    """
    editor = AtomoEditor(stdscr, filename)
    editor.run()


# Punto di ingresso del programma
if __name__ == "__main__":
    # Ottiene il nome del file dagli argomenti della riga di comando
    filename = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        # curses.wrapper() si occupa di:
        # - Inizializzare curses
        # - Chiamare main()
        # - Ripristinare il terminale anche in caso di errori
        curses.wrapper(main, filename)
    except KeyboardInterrupt:
        # Gestisce Ctrl+C
        print("\nExited.")
    except Exception as e:
        # Gestisce altri errori
        print(f"Error: {e}")
        sys.exit(1)
