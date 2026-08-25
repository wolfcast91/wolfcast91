# Datenbedarf — was ich von dir brauche

Ausfüllen, wo möglich. `?` stehen lassen, wo du es nicht weißt — ich sage dir dann,
ob es kritisch ist oder ob ich es abschätzen kann.

---

## MINIMALPAKET (ohne das geht gar nichts — 8 Angaben)

Wenn du nur zehn Minuten hast, dann diese acht:

1. **Gerätetyp / Typenschild**: Vitovalor PT2 Typ `______` (F11T / F19T / F25T / F32T?)
2. **Gasarbeitspreis** brutto: `____` ct/kWh  — und Grundpreis `____` €/Jahr
3. **Strombezugspreis** brutto: `____` ct/kWh — und Grundpreis `____` €/Jahr
4. **Einspeisevergütung PV**: `____` ct/kWh
5. **KWK-Vergütung BZ**: Zuschlag Eigenverbrauch `____` ct/kWh, Einspeisung `____` ct/kWh
   (steht auf der Jahresabrechnung des Netzbetreibers)
6. **Jahresstromverbrauch Haushalt**: `____` kWh/a
7. **Jahresgasverbrauch gesamt**: `____` kWh/a
8. **Wartungsvertrag**: Vollwartung ja/nein? Kosten `____` €/a. Ist ein Stacktausch
   enthalten? ja/nein

---

## A — Anlagenkonfiguration

- Baujahr / Inbetriebnahme der PT2: `______`
- Bisherige Betriebsstunden der Brennstoffzelle: `______` h
  *(ViCare bzw. Regelung → Statistik/Betriebsdaten)*
- Firmware-/Regelungsstand: `______`
- Zusätzlicher Heizwasser-Pufferspeicher vorhanden? ja/nein, `____` Liter
- Hydraulische Weiche vorhanden? ja/nein
- Heizkreise: Fußbodenheizung / Heizkörper / gemischt — Anteile `______`
- Auslegungs-Vorlauf/Rücklauf: `____` / `____` °C
- Zirkulationspumpe Warmwasser: ja/nein, Laufzeiten `______`
- Solarthermie vorhanden? ja/nein

## B — Gebäude & Wärmebedarf

- Wohnfläche beheizt: `____` m²
- Baujahr / Dämmstandard: `______`
- Personen im Haushalt: `____`
- Heizlast (falls bekannt, aus Heizlastberechnung): `____` kW
- Aktuelle Heizkurve: Neigung `____` / Niveau `____`
- Nachtabsenkung: aktiv ja/nein, von `____` bis `____` Uhr, Absenkung `____` K
- Warmwasser-Solltemperatur: `____` °C, Ladezeiten `______`

## C — PV & Batteriespeicher

- PV: 2 kWp — Ausrichtung `______`, Neigung `____`°, Verschattung `______`
- Jahresertrag PV real: `____` kWh/a (und wenn möglich: Monatswerte)
- Wechselrichter Hersteller/Modell: `______`
- Batteriespeicher 4 kWh: Hersteller/Modell `______`
- **AC- oder DC-gekoppelt?** `______`
- **Kann der Akku aus AC-Überschuss (also aus der Brennstoffzelle) geladen werden?**
  ja / nein / weiß nicht  ← **das ist die wichtigste Einzelfrage für Hebel H4**
- Kann der Akku aus dem Netz geladen werden (Zwangsladung/Zeitplan)? ja/nein
- Entladetiefe / nutzbare Kapazität: `____` kWh
- Welches EMS steuert den Akku? `______`

## D — Messtechnik & Verschaltung (für Hebel H5)

- Zählerkonzept: ein Zweirichtungszähler? separater BZ-Erzeugungszähler? Skizze/Beschreibung
- Welcher Messpunkt sieht der **BZ-Energiemanager**? `______`
- Welcher Messpunkt sieht das **Akku-EMS**? `______`
- Smart Meter / Shelly / Home Assistant / evcc im Einsatz? `______`
- Hast du eine Anbindung, aus der ich Zeitreihen ziehen kann?
  (ViCare-App-Export, Viessmann API, Home Assistant, PV-Portal)

## E — Ist-Betriebsdaten (das Wertvollste)

Je feiner die Auflösung, desto belastbarer die Empfehlung.

**Pflicht (Monatswerte, letzte 12 Monate):**
- Stromerzeugung BZ: `____` kWh/Monat
- Netzbezug: `____` kWh/Monat
- Netzeinspeisung: `____` kWh/Monat
- Gasverbrauch gesamt: `____` kWh/Monat
- BZ-Betriebsstunden: `____` h/Monat
- Anzahl BZ-Starts: `____` /Monat  ← **wichtig, zeigt Taktung**

**Sehr wertvoll, falls verfügbar:**
- Lastgang Haushalt in 15-min-Auflösung, mindestens eine typische Winterwoche
- PV-Erzeugung 15-min, gleiche Woche
- Akku-SoC-Verlauf, gleiche Woche
- Vorlauf-/Rücklauftemperatur-Verlauf, gleiche Woche
- Speichertemperatur-Verlauf

CSV/Excel ins Repo legen oder hochladen — ich rechne das dann durch.

## F — Verträge, Förderung, Recht

- Netzbetreiber: `______`
- KWKG-Zulassung (BAFA) vorhanden, Fördersatz/Restlaufzeit: `______`
- Energiesteuerentlastung nach §53a EnergieStG beantragt? ja/nein
  *(falls nein: das ist bares Geld, das du liegen lässt)*
- Gasliefervertrag: Laufzeit bis `______`, Preisbindung?
- Stromliefervertrag: Laufzeit bis `______`
- Dynamischer Stromtarif verfügbar/erwogen? ja/nein
  *(ändert die Strategie erheblich — dann wird Einspeisezeitpunkt steuerbar)*

## G — Randbedingungen & Präferenzen

- Zielgröße: minimale **Kosten** / minimale **CO₂** / maximale **Autarkie**?
  (bei Konflikt: was gewinnt?)
- Komfortgrenzen: minimale Raumtemperatur, akzeptable WW-Wartezeit
- Bist du bereit, in die **Fachmann-Ebene** der Regelung zu gehen
  (Codieradressen, Passwort `viservice`)? ja/nein
- Elektroauto vorhanden/geplant? `______`
- Wärmepumpe als Ergänzung erwogen? `______`
- Wie viel manuelles Nachsteuern ist ok — einmal pro Saison, monatlich, automatisiert?

## H — Dokumente

Wenn du mir eins von diesen als PDF gibst, wird die Analyse deutlich präziser
(die Netzwerk-Policy hier blockt den Direktdownload von viessmann.de):

- [ ] Bedienungsanleitung Vitovalor PT2
- [ ] **Planungsanleitung Vitovalor PT2** ← am wertvollsten, enthält die Betriebsmodi-Parametrierung
- [ ] Inbetriebnahmeprotokoll / Wartungsprotokoll
- [ ] Letzte Jahresabrechnung Netzbetreiber (KWK-Abrechnung)
- [ ] Hydraulikschema der Anlage

---

## Was ich dir liefere, sobald das da ist

1. Grenzkostenkurve deiner Anlage über die Heizperiode (statt der generischen Tabelle)
2. Konkrete Umschaltschwellen: ab welcher Außentemperatur / welchem Tagesmittel
   welcher Betriebsmodus
3. Konkrete Parametersätze: Heizkurve, Nachtabsenkung, WW-Ladefenster,
   Regenerationsfenster
4. Akku-Strategie Winter (Laden aus BZ-Überschuss, ja/nein/wie)
5. Eine Rechnung: erwartete Ersparnis gegenüber deinem Ist-Betrieb, in €/Heizperiode
