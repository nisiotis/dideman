# -*- coding: utf-8 -*-
"""Κωδικοποιήσεις εξαγόμενων αρχείων.

Τα αρχεία που παράγει η εφαρμογή ανοίγονται είτε σε σύγχρονα εργαλεία
(UTF-8) είτε σε παλαιότερες εγκαταστάσεις του Excel σε ελληνικά Windows,
που περιμένουν ISO-8859-7 / Windows-1253. Το module κρατάει σε ένα σημείο
τα διαθέσιμα σετ χαρακτήρων και την μετατροπή των τιμών, ώστε κάθε νέα
εξαγωγή να προσφέρει τις ίδιες επιλογές.
"""

UTF8 = 'utf-8'
GREEK_WINDOWS = 'cp1253'

# (κωδικός, ετικέτα για τον χρήστη). Η σειρά είναι και η σειρά εμφάνισης.
ENCODING_CHOICES = [
    (UTF8, 'UTF-8 (Unicode)'),
    (GREEK_WINDOWS, 'Ελληνικά Windows (Windows-1253)'),
]

DEFAULT_ENCODING = UTF8

# Το BOM βοηθάει το Excel να αναγνωρίσει UTF-8 αρχείο· χωρίς αυτό ανοίγει
# το CSV σαν ANSI και τα ελληνικά εμφανίζονται αλλοιωμένα. Είναι ο
# χαρακτήρας U+FEFF, που κωδικοποιείται σε EF BB BF μόνο στην UTF-8· στα
# ελληνικά Windows δεν μπαίνει BOM.
BOM = {UTF8: '\ufeff'}

# Πώς δηλώνεται η κάθε κωδικοποίηση στην κεφαλίδα HTTP.
CHARSET = {
    UTF8: 'utf-8',
    GREEK_WINDOWS: 'windows-1253',
}


def is_supported(encoding):
    return encoding in dict(ENCODING_CHOICES)


def clean_encoding(encoding):
    """Δέχεται τιμή από φόρμα και επιστρέφει πάντα έγκυρη κωδικοποίηση."""
    return encoding if is_supported(encoding) else DEFAULT_ENCODING


def charset_name(encoding):
    """Το όνομα που μπαίνει στο Content-Type."""
    return CHARSET.get(clean_encoding(encoding), CHARSET[DEFAULT_ENCODING])


def bom_for(encoding):
    """Ο χαρακτήρας που πρέπει να προηγηθεί του αρχείου, αν χρειάζεται."""
    return BOM.get(clean_encoding(encoding), '')


def encode(value, encoding=DEFAULT_ENCODING, errors='replace'):
    """Μετατρέπει κείμενο σε bytes της ζητούμενης κωδικοποίησης.

    Χαρακτήρες που δεν υπάρχουν στο ελληνικό σετ αντικαθίστανται αντί να
    πετάγονται σιωπηλά, ώστε να φαίνεται ότι κάτι χάθηκε. Καλείται μία
    φορά στο τέλος: στην Python 3 το csv module δουλεύει με κείμενο, όχι
    με bytes.
    """
    encoding = clean_encoding(encoding)
    if value is None:
        return b''
    if isinstance(value, bytes):
        return value
    return str(value).encode(encoding, errors)
