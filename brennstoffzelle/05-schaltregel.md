# Conclusion: Wann die BZ an und aus gehört

Basis: ViCare-Gasverbrauch Aug 2025 – Jul 2026 (Januar exakt: 252 m³ gesamt,
davon BZ 145 m³, Spitzenlastkessel 107 m³; Jahr 1.406 m³) + Stromerzeugung
+ Gas 10,16 ct/kWh, Tibber Ø 27 ct/kWh, kein Wartungsvertrag.

## Korrektur vorab

Meine Grenzkosten von 11,79 ct/kWh waren falsch — ich hatte Brennwert (Hs, so wird
abgerechnet) und Heizwert (Hi, so steht die Geräteleistung im Datenblatt) vermischt.
Sauber gerechnet, an deinen Januardaten kalibriert:

```
BZ-Gasaufnahme 2,19 kW (Hs) = 0,212 m³/h
145 m³ / 0,212 = 683 Betriebsstunden im Januar = 92 % Laufzeit
683 h × 0,75 kW = 512 kWh Strom   (ViCare zeigt 495 kWh — Modell bestätigt)
```

**Grenzkosten bei voller Wärmenutzung: 14,41 ct/kWh**, mit Energiesteuerentlastung
§53a **13,63 ct/kWh**. Nicht 11,79 ct. Das verschiebt den Break-even für eingespeisten
Strom entsprechend nach oben.

## Was deine Anlage tatsächlich tut

| Monat | m³/Tag | BZ h/Tag | Laufzeit | Wärmebedarf kWh_th/Tag | ÷ BZ-Kapazität |
|---|---|---|---|---|---|
| Aug 25 | 0,97 | 0,3 | 1 % | 9,5 | 0,36× |
| Sep | 1,20 | 0,8 | 3 % | 11,3 | 0,43× |
| **Okt** | 3,97 | 12,6 | **53 %** | 26,9 | **1,02×** |
| Nov | 7,07 | 21,5 | 90 % | 48,9 | 1,85× |
| Dez | 7,84 | 22,3 | 93 % | 55,8 | 2,11× |
| Jan | 8,13 | 22,0 | 92 % | 59,1 | 2,24× |
| Feb | 6,61 | 20,9 | 87 % | 44,9 | 1,70× |
| **Mrz** | 5,03 | 17,0 | **71 %** | 33,0 | **1,25×** |
| Apr | 3,13 | 11,1 | 46 % | 20,0 | 0,76× |
| Mai–Jul | ~1,0 | 0 | 0 % | ~10 | 0,38× |

Zwei Ablesungen daraus:

- **Die BZ liefert bei Dauerlauf 26,4 kWh_th/Tag.** Deine Warmwasser-Grundlast
  (Sommer, BZ aus) liegt bei **~9–11 kWh_th/Tag**. Alles darüber ist Heizwärme.
- **Oktober und März haben ungenutztes Potenzial.** Im Oktober reichte der Wärmebedarf
  für Dauerlauf (1,02×), die BZ lief aber nur 53 %. Im März 1,25× bei 71 % Laufzeit.
  Hier — nicht im Januar — greifen die Wärmesenken-Hebel aus Dokument 01
  (Nachtabsenkung, Heizkurve, WW-Entkopplung).

## Die Schaltregel

Der begrenzende Faktor ist nicht die Wärme, sondern die **Starts**. Die BZ vergeudet
keine Wärme (sie stoppt, wenn keine Senke da ist), aber jeder Start kostet ~75 min
Anlauf und ~1,2 kWh Strom. Sobald der Wärmebedarf nur noch einen Block pro Tag trägt,
steigen die effektiven Grenzkosten:

| Monat | Starts/Monat | Effektive Grenzkosten | Nötiger Einspeiseerlös* |
|---|---|---|---|
| Nov–Feb | 14–16 (regenerationsbedingt) | **14,6 ct** | 8,0 ct |
| März | ~31 (täglich) | 16,2 ct | 10,3 ct |
| Oktober | ~31 (täglich) | 17,1 ct | 11,7 ct |
| April | ~30 (täglich) | 17,5 ct | 12,4 ct |

\* damit sich der Betrieb trägt, bei 35 % Eigenverbrauchsanteil

### Einschalten — Anfang bis Mitte Oktober

Auslöser: **Gaszähler (BZ noch aus) übersteigt ~2,7 m³/Tag** im Schnitt über 3–4 Tage.
Entspricht ~27 kWh_th/Tag, also dem Punkt, ab dem die BZ durchlaufen kann.
Als Faustregel am Wetter: **Tagesmitteltemperatur mehrere Tage unter ~10 °C.**

Dein September lag bei 1,20 m³/Tag — deutlich darunter, korrekt aus.
Dein Oktober lag bei 26,9 kWh_th/Tag — genau an der Schwelle, korrekt an.

### Ausschalten — Mitte bis Ende April

Auslöser: **Wärmebedarf fällt unter ~20 kWh_th/Tag** (BZ trägt dann keinen
durchgehenden Block mehr). Bei laufender BZ heißt das grob **unter 3 m³/Tag gesamt**.
Am Wetter: **Tagesmittel dauerhaft über ~12 °C.**

Dein April lag bei **20,0 kWh_th/Tag und 46 % Laufzeit mit ~30 Starts** — das ist genau
die Zone, in der es kippt. Effektive Grenzkosten 17,5 ct gegen einen Mischwert, der
bei 8 ct Einspeisung nur ~14 ct erreicht.

**→ Die konkreteste Änderung an deinem bisherigen Fahrplan: April früher beenden.**
Statt Ende April eher Mitte April, bei mildem Frühjahr auch Anfang April.

### Zusammengefasst

| | bisher | Empfehlung |
|---|---|---|
| An | Oktober | **Oktober** (bleibt) |
| Aus | Ende April | **Mitte April** |
| Laufzeit Okt/Mrz | 53 % / 71 % | **auf 80–90 % anheben** über Wärmesenke |
| Mai–Sep | Standby | **Standby** (bestätigt) |

## Was die Anlage verdient

Januar, 512 kWh, davon 199 kWh Eigenverbrauch, inkl. 4 ct KWK-Zuschlag auf
Eigenverbrauch und Energiesteuerentlastung:

| Einspeiseerlös | Januar-Ergebnis |
|---|---|
| 8 ct | +16,93 € |
| 12 ct | +29,45 € |
| 16 ct | +41,97 € |

**Die eine Zahl, die noch fehlt, ist der Einspeiseerlös** (Netzbetreiber-Abrechnung:
üblicher Preis + KWK-Zuschlag + vermiedene Netznutzungsentgelte). Sie entscheidet
über Faktor 2,5 im Ergebnis — und darüber, ob Oktober/März/April überhaupt
kostendeckend laufen. Bei ≥12 ct sind alle Monate Okt–Apr sauber im Plus, bei 8 ct
tragen sich nur November bis Februar.

## Rangfolge

1. **Einspeiseerlös ermitteln** — entscheidet über alles Weitere
2. **Energiesteuerentlastung §53a** — 1.493 kWh BZ-Gas im Januar = 8,21 €; über die
   Heizperiode ~45 €/a, ohne jeden Eingriff an der Anlage
3. **April verkürzen** — spart die teuersten Betriebsstunden des Jahres
4. **Oktober/März-Laufzeit anheben**: WW entkoppeln (Therme 45–48 °C, BZ bis 58–60 °C),
   Nachtabsenkung flach, Heizkurve niedrig. Genau hier liegt die Reserve, nicht im Januar
5. **Akku auf BZ-Überschuss** laden, Entladung in teure Tibber-Stunden (~8 €/Monat)
