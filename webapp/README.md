# DRMD Webapp (Integrated)

Diese Streamlit-Anwendung wurde aus `mehranmo/drmd-webapp-2` importiert und an die monolithische Schema-/XSL-Struktur dieses Repos angepasst.

## Start

```bash
pip install -r webapp/requirements.txt
streamlit run webapp/app.py
```

Die Anwendung verwendet:
- Schema: `xsd/drmd.xsd`
- XSLT: `xsl/drmd.xsl`

Änderungen gegenüber Original:
- Pfade zu Schema/XSL zentralisiert
- App-Code als dynamisch importiertes Modul (`webapp_src/app.py`) belassen für bessere Nachverfolgbarkeit
- Namespace-Konstante bleibt `https://example.org/drmd` (bitte anpassen falls sich `targetNamespace` ändert)

## TODO
- UI an Option-A Datentyp-Anpassungen prüfen
- Validierungs-Feedback vereinheitlichen
