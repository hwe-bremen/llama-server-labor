Schreib ein Python-Skript `gguf_lesen.py`, das den Kopf einer GGUF-Datei (Dateiformat von llama.cpp, Version 3, little-endian) liest und als JSON ausgibt.

Harte Vorgaben:
- Nur die Python-Standardbibliothek (Python 3.11+). Kein `gguf`, kein `numpy`, keine anderen Pakete.
- Aufruf: `python3 gguf_lesen.py <pfad>`. Ausgabe: genau ein JSON-Objekt auf stdout, sonst nichts.
- Die Dateien können über 50 GB groß sein. Lies nur Kopf, Metadaten und Tensor-Infos, nicht die Tensordaten. Die Dateigröße über das Dateisystem bestimmen.
- Du hast keinen Zugriff auf Dokumentation oder das Internet. Arbeite aus deinem Wissen über das Format.
- Kennt dein Skript einen Tensortyp nicht, darf es nicht abstürzen: dann `"type": "UNBEKANNT"` und `"n_bytes": null`.

JSON-Schema der Ausgabe:
```
{
  "version": <int>,
  "tensor_count": <int>,
  "kv_count": <int>,
  "alignment": <int>,            // tatsächlich geltendes Alignment der Tensordaten in Byte
  "data_offset": <int>,          // absolute Dateiposition, an der die Tensordaten beginnen
  "metadata": {
    "<schluessel>": {"type_id": <int>, "value": <wert>},
    // Arrays stattdessen:
    "<schluessel>": {"type_id": <int>, "item_type_id": <int>, "len": <int>, "value": [<höchstens die ersten 8 Elemente>]}
  },
  "tensors": [
    {"name": <str>, "shape": [<int>, ...], "type": <str>, "type_id": <int>, "offset": <int>, "n_bytes": <int oder null>}
  ],
  "end": <int>,                  // absolute Dateiposition direkt hinter dem letzten Byte der Tensordaten
  "file_size": <int>,
  "ok": <bool>                   // true, wenn end <= file_size und file_size - end < alignment
}
```

Erläuterungen:
- `type_id` / `item_type_id`: die numerische ID des GGUF-Metadaten-Werttyps, so wie sie in der Datei steht.
- `value`: Zahlen als JSON-Zahl, Wahrheitswerte als JSON-Boolean, Zeichenketten als JSON-String (UTF-8). Verschachtelte Arrays (Array von Arrays) müssen gelesen werden können; ein inneres Array wird als Objekt mit `item_type_id`, `len`, `value` dargestellt.
- `metadata` enthält alle Schlüssel-Wert-Paare der Datei, ohne die Kopfzähler.
- `shape`: Dimensionen in der Reihenfolge, in der sie in der Datei stehen.
- `type`: der ggml-Typname in Großbuchstaben, wie in llama.cpp (z. B. `F32`). `type_id`: die numerische ggml-Typ-ID aus der Datei.
- `offset`: der Offset-Wert aus der Tensor-Info, unverändert.
- `n_bytes`: Größe der Tensordaten in Byte, aus Form und Typ berechnet (ohne Auffüllung).

Liefere den vollständigen Code in genau einem ```python-Block. Keine Rückfragen.
