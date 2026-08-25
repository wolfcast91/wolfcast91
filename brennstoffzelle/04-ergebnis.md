# Ergebnis und Handlungsempfehlung

Bestätigt: **2.500 kWh/a = Gesamtverbrauch** (nicht Netzbezug). Die Sommerbalken im
ViCare-Diagramm sind die **PV-Anlage**, nicht die Brennstoffzelle.

## 1. Die Lage in einem Satz

Deine Brennstoffzelle produziert im Januar 495 kWh, dein Haushalt braucht im selben
Monat rund 229 kWh. **Die Anlage ist für deinen Verbrauch etwa doppelt so groß wie
nötig** — und damit ist die Wirtschaftlichkeit fast vollständig eine Frage der
Einspeisevergütung, nicht der Betriebsführung.

Die BZ deckt bereits **87 % deines Januarverbrauchs direkt**. Es bleiben ~30 kWh
Netzbezug im Monat — das ist der gesamte verbleibende Eigenverbrauchshebel, wert
maximal **8 €/Monat**, und den kann dein Akku größtenteils holen.

## 2. Monatsergebnis Januar, in Abhängigkeit vom Einspeiseerlös

Grenzkosten bei voller Wärmenutzung: **11,79 ct/kWh**
Eigenverbrauch 199 kWh × (27 − 11,79) ct = **+30,28 €**

| Einspeiseerlös | Ergebnis Einspeisung | Januar gesamt | mit Energiesteuerentlastung |
|---|---|---|---|
| 0 ct | −34,77 € | −4,49 € | +2,66 € |
| 8 ct | −11,17 € | +19,11 € | **+26,26 €** |
| 12 ct | +0,63 € | +30,91 € | +38,06 € |
| 16 ct | +12,43 € | +42,71 € | +49,86 € |

**Der gesamte Gewinn der Anlage hängt an dieser einen Zahl.** Bei 8 ct fressen die
eingespeisten kWh ein Drittel des Eigenverbrauchsgewinns wieder auf. Bei 0 ct arbeitet
die Anlage im Winter bei null.

→ **Zu besorgen: Jahresabrechnung des Netzbetreibers.** Erlös je eingespeister kWh
inkl. KWK-Zuschlag und vermiedener Netznutzungsentgelte.

## 3. Geprüft und verworfen: BZ auf Eigenbedarf drosseln

Naheliegende Idee bei 60 % Einspeisung: BZ nur so lange laufen lassen, wie der
Haushalt braucht (8,6 h/Tag statt 21,3 h/Tag, ein Start pro Tag).

| Posten | Betrag |
|---|---|
| Vermiedener Einspeiseverlust @ 8 ct | +11,17 €/Monat |
| Startenergie 31 × ~1,2 kWh × 27 ct | −10,04 €/Monat |
| Stack-Alterung durch 31 Thermozyklen/Monat | nicht quantifiziert, aber real |

**Hebt sich auf, mit negativem Rest.** Thermische Zyklen sind der Haupt-Alterungstreiber
bei PEM-Brennstoffzellen, und du hast **keinen Wartungsvertrag** — der Stack geht auf
deine Rechnung. Also: **nicht drosseln, durchlaufen lassen.**

Damit steht die Winterstrategie fest, unabhängig vom Einspeisetarif.

## 4. Die Standby-Schwelle — hier liegt der echte Hebel

Nicht im Kernwinter, sondern in der **Übergangszeit**. Sobald die Wärmenutzung sinkt,
steigen die Grenzkosten steil:

```
Grenzkosten(u) = 26,69 − 14,90 · u   [ct/kWh_el]
```

Bei einem Eigenverbrauchsanteil von ~45 % in der Übergangszeit:

| Einspeiseerlös | Break-even bei | Standby, wenn Wärmebedarf unter |
|---|---|---|
| 8 ct | u = 0,68 | **~18 kWh_th/Tag ≈ 1,8 m³ Gas/Tag** |
| 16 ct | u = 0,38 | **~10 kWh_th/Tag ≈ 1,0 m³ Gas/Tag** |

**Das ist am Gaszähler ablesbar.** Konkrete Regel für Herbst und Frühjahr: Gaszähler
über drei bis vier Tage mitschreiben. Fällt der Tagesverbrauch unter die Schwelle,
BZ in Standby — und zwar eher zu früh als zu spät, weil jeder zusätzliche Start-Stopp-
Zyklus separat kostet.

Praktisch heißt das: **BZ später einschalten und früher abschalten**, als das Gefühl
sagt. Im Zweifel Anfang Oktober an, Anfang April aus.

## 5. Warmwasser 55 °C — Entkopplung bleibt richtig

| Parameter | Einstellung |
|---|---|
| WW-Soll / Freigabe Brennwertmodul | 45–48 °C |
| Max. Speichertemperatur / Wärmeabnahme BZ | 58–60 °C |

Die Therme lädt nur bis 45–48 °C → niedriger Rücklauf, Brennwerteffekt bleibt. Die
letzten 10 K macht die BZ mit ohnehin anfallender Wärme. 220 l × 10 K = 2,56 kWh
Zusatzpuffer = 2,3 h zusätzliche BZ-Laufzeit. Im Sommer (BZ Standby) wieder auf 45 °C.

Hygiene: 45 °C Dauertemperatur in 220 l liegt im Legionellen-Wachstumsbereich. W551
verlangt bei EFH keine 60 °C, aber 55 °C ist deutlich unkritischer.

## 6. Getrennte Baustelle: die PV-Anlage

Aus dem Diagramm abgelesen liefern die Sommermonate nur **~30–60 kWh/Monat**. Für
2 kWp sind im Juni **180–250 kWh** zu erwarten — selbst mit Ost-West-Ausrichtung noch
~150 kWh. Der abgelesene Wert liegt um den Faktor 3–8 darunter.

Entweder
- die PV läuft schlecht (Verschattung, Wechselrichter-Begrenzung, Defekt, String-Fehler), oder
- ViCare sieht nur einen Teil der Erzeugung (Messpunkt hinter dem Akku o. ä.).

**Das ist potenziell mehr wert als die gesamte BZ-Feinoptimierung.** 150 kWh/Monat
Differenz über die Sommermonate sind bei 27 ct schnell 100–150 €/Jahr.

Prüfen: Jahresertrag der PV laut Wechselrichter-Portal gegen die ViCare-Zahlen halten.

## 7. Reihenfolge des Handelns

1. **Energiesteuerentlastung §53a EnergieStG** prüfen — im Januar allein 7,15 €,
   über die Heizperiode ~45 €/a. Reines Papier, kein Eingriff an der Anlage.
2. **Einspeiseerlös aus der Netzbetreiber-Abrechnung ermitteln** — entscheidet, ob
   die Anlage 27 € oder 50 € im Wintermonat verdient, und setzt die Standby-Schwelle.
3. **PV-Ertrag gegenprüfen** — möglicherweise der größte Einzelposten.
4. **WW-Temperaturen entkoppeln** (45–48 / 58–60 °C).
5. **Akku auf BZ-Überschuss laden lassen**, Entladung in die teuren Tibber-Stunden.
   Deckelt bei ~8 €/Monat im Winter, mehr im Sommer.
6. **Standby-Schwelle nach Gaszähler** fahren statt nach Kalender.

Die Heizungs-Feinjustage (Nachtabsenkung, Heizkurve) aus `01-anlage-und-hebel.md` ist
damit **nachrangig** — im Kernwinter ist die Laufzeit ohnehin nahe am Maximum.

## Offen

- Enthält das ViCare-Diagramm **BZ + PV zusammen** oder nur die BZ? Falls zusammen,
  liegt die BZ-Erzeugung im Januar bei ~460 statt 495 kWh (Laufzeit 82 % statt 89 %) —
  dann gäbe es doch ~90 kWh/Monat Laufzeitreserve, wert ~14 €/Monat, und die
  Wärmesenken-Hebel aus Dokument 01 wären wieder relevant.
- Alter der Anlage und Betriebsstundenzähler (KWK-Zuschlag läuft nach 60.000
  Vollbenutzungsstunden aus, bei ~4.000 h/a also nach ~15 Jahren).
