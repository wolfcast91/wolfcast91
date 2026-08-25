# Auswertung mit deinen Ist-Daten

Datenstand: ViCare-Screenshot Stromerzeugung, Aug 2025 – Jul 2026 (abgelesen 25.08.2026)
Preise: Gas 10,16 ct/kWh · Strom Tibber Ø 27 ct/kWh · kein Wartungsvertrag · Akku AC-ladefähig

## 1. Was die Zahlen sagen

**Januar 2026:** 495 kWh erzeugt, davon 295 kWh eingespeist (59,6 %), 199 kWh direkt verbraucht.

| Kennzahl | Wert |
|---|---|
| Betriebsstunden Januar | 660 h (aus 495 kWh / 0,75 kW) |
| Laufzeitquote | 88,7 % des Monats |
| Theoretisches Maximum (mit 2,5 h Regeneration je 45,5 h) | 705 h = 529 kWh |
| **Ausschöpfung des Maximums** | **93,6 %** |
| Wärme erzeugt | 726 kWh_th |
| Gas in die BZ | 1.300 kWh |
| Direktverbrauch | 6,4 kWh/Tag |
| Einspeisung | 9,5 kWh/Tag |

**Jahr Aug 25 – Jul 26:** 3.120 kWh → 4.160 Betriebsstunden (47 % des Jahres),
8.195 kWh Gas in die BZ, 4.576 kWh_th Abwärme.

### Befund 1 — Der Laufzeithebel ist bereits ausgereizt

Im Januar läuft die BZ zu 93,6 % dessen, was physikalisch möglich ist. Die Hebel aus
`01-anlage-und-hebel.md` (Nachtabsenkung, Heizkurve, Wärmesenke) bringen im Kernwinter
**maximal 34 kWh/Monat** — bei 15 ct Marge sind das gut 5 € im Monat. Nicht null, aber
nicht der Hauptpunkt. Die ursprüngliche Winter-Hypothese "so lange wie möglich laufen
lassen" ist bei dir bereits erfüllt.

### Befund 2 — Das Problem ist die Verwertung, nicht die Erzeugung

**60 % der Januar-Produktion geht ins Netz.** Das ist die eigentliche Baustelle.

Und der Akku löst es nur zum Teil: 9,5 kWh/Tag Überschuss stehen 4 kWh nutzbarer
Akkukapazität gegenüber. Selbst bei perfekter täglicher Vollzyklung bleiben
**≥ 5,5 kWh/Tag Einspeisung** übrig. Das ist strukturell — die BZ ist mit 750 W
Dauerleistung (= 6.570 kWh/a Potenzial) für deinen Haushalt schlicht groß.

### Befund 3 — Sommermonate sind nicht auf null

Aus dem Diagramm grob abgelesen: Jun/Jul/Aug 2026 zeigen noch ~30–60 kWh/Monat.
Trotz "Standby" lief die BZ also 40–80 h. Bei u≈0 kostet jede dieser kWh ~26,7 ct —
also etwa Netzstrompreis, ohne jeden Vorteil. Zu klären, ob das Erhaltungs-/
Regenerationsläufe sind (unvermeidbar) oder vermeidbare Starts.

## 2. Grenzkosten mit deinen Preisen

```
g(u) = (1,97 − u · 1,1) / 0,75   kWh Gas je kWh Strom
```

| Wärmenutzung | kWh Gas/kWh el | Grenzkosten @ 10,16 ct |
|---|---|---|
| 100 % (Kernwinter) | 1,16 | **11,79 ct** |
| 75 % | 1,53 | 15,51 ct |
| 50 % (Übergang) | 1,89 | 19,24 ct |
| 0 % (Sommer) | 2,63 | 26,69 ct |

Mit Energiesteuerentlastung §53a (0,55 ct/kWh_Gas): **11,15 ct/kWh** im Kernwinter.

- **Eigenverbrauchte kWh:** spart 27 − 11,8 = **+15,2 ct/kWh**. Eindeutig gut.
- **Eingespeiste kWh:** Break-even bei **11,8 ct/kWh Erlös** (11,15 mit Steuerentlastung).

### Die eine entscheidende offene Zahl

**Was bekommst du pro eingespeister BZ-kWh?** (Vergütung + KWK-Zuschlag +
vermiedene Netznutzungsentgelte, aus der Netzbetreiber-Jahresabrechnung)

- Liegt der Erlös **über ~11,8 ct** → die 295 kWh Einspeisung sind profitabel,
  Strategie bleibt "Vollgas im Winter", der Akku ist nur noch Feinoptimierung.
- Liegt er **darunter** → jede eingespeiste kWh ist ein Verlustgeschäft, und die
  Strategie kippt komplett: BZ-Laufzeit gezielt am Eigenverbrauch ausrichten statt
  am Wärmebedarf.

Bei 295 kWh/Monat entscheidet das über einen zweistelligen Eurobetrag pro Wintermonat.

**Nebenpunkt:** Der KWK-Zuschlag ist auf 60.000 Vollbenutzungsstunden begrenzt. Bei
4.160 h/a sind das ~14 Jahre. Wie alt ist die Anlage?

## 3. Warmwasser 55 °C vs. Therme 45 °C

Dein Effizienzbedenken ist im **Sommer** richtig und im **Winter** weitgehend
gegenstandslos. Drei Gründe:

1. **Speicherverluste sind im Winter keine Verluste.** Der 220-l-Speicher steht in der
   thermischen Hülle. Was er abstrahlt, spart Heizenergie. Die Mehrverluste von 45→55 °C
   (~0,6–0,8 kWh/Tag) landen in der Heizung. Im Sommer sind sie echter Verlust — dort
   sind 45 °C plus BZ-Standby richtig.

2. **Die höhere Speichertemperatur ist Puffer, kein Nachteil.** 220 l von 45 auf 55 °C
   = **2,56 kWh Zusatzspeicher = 2,3 h zusätzliche BZ-Laufzeit**, bevor die BZ mangels
   Wärmesenke abregelt. Das ist genau die Reserve, die die 93,6 % Ausschöpfung trägt.

3. **Der Brennwertverlust entsteht nur, wenn die *Therme* auf 55 °C lädt.** Wenn die
   BZ die letzten 10 K macht, bleibt der Therme-Rücklauf niedrig und der Brennwerteffekt
   erhalten.

**Konkreter Fix — Temperaturen entkoppeln:**

| Parameter | Einstellung | Wirkung |
|---|---|---|
| WW-Solltemperatur (Freigabe Brennwertmodul) | 45–48 °C | Therme lädt nur bis hier → niedriger Rücklauf, voller Brennwerteffekt |
| Max. Speichertemperatur / Wärmeabnahme BZ | 58–60 °C | BZ darf durchladen → Puffer + Laufzeit, kostenlos |

Damit bekommst du beides: Brennwertbetrieb der Therme *und* den großen Puffer für die BZ.
Die exakten Parameternamen stehen in der Planungsanleitung (Fachmann-Ebene, Passwort
`viservice`) — die konnte ich hier nicht laden.

**Hygiene-Hinweis:** 45 °C Dauertemperatur in einem 220-l-Speicher liegt mitten im
Legionellen-Wachstumsbereich. Für Ein-/Zweifamilienhäuser schreibt DVGW W551 zwar keine
60 °C vor, aber 55 °C ist deutlich unkritischer als 45 °C. Das spricht zusätzlich dafür,
den Speicher von der BZ hochladen zu lassen.

## 4. Offene Frage mit großer Hebelwirkung

**Sind die 2.500 kWh dein Netzbezug oder dein Gesamtverbrauch?**

- **Netzbezug 2.500 kWh/a:** Dann kaufst du ~6,8 kWh/Tag ein, während die BZ
  9,5 kWh/Tag einspeist. Das wäre ein handfester Regelungs- oder Messfehler —
  vermutlich sieht der BZ-Energiemanager deine Last nicht richtig, oder BZ und Akku
  hängen messtechnisch aneinander vorbei (Hebel H5). Da läge dann sehr viel Geld.
- **Gesamtverbrauch 2.500 kWh/a:** Dann deckt die BZ im Januar bereits 85 % deines
  Bedarfs direkt, der Netzbezug liegt bei ~1 kWh/Tag, und es gibt beim Eigenverbrauch
  fast nichts mehr zu holen. Die Optimierung reduziert sich auf die Einspeisefrage
  aus Abschnitt 2.
