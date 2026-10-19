# Tipografías del PDF de pauta

Quicksand (títulos) y Nunito (texto), licencia SIL Open Font License 1.1
(ver `OFL-*.txt`). Fuente: repositorio oficial google/fonts (`ofl/quicksand`,
`ofl/nunito`), versiones variables `[wght]` instanciadas a estáticas con
`fontTools.varLib.instancer` (Quicksand 700; Nunito 400, 600, 700), porque
ReportLab no soporta fuentes variables.

`backend/pdf_pauta.py` las usa si existen; si no, cae a Helvetica.
