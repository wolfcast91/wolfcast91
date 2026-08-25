# Vitovalor PT2 — Betriebsstrategie Herbst/Winter

Stand: 2026-08-25

## 0. Quellenlage (wichtig für die Bewertung)

Die Original-PDFs von Viessmann (Bedienungsanleitung, Planungsanleitung, Datenblatt)
konnten in dieser Session **nicht direkt geladen werden** — die Netzwerk-Policy blockt
`viessmann.de`, `community.viessmann.de`, `manualslib.de` u.a. Die technischen Eckwerte
unten stammen aus Websuche-Auswertungen dieser Dokumente, nicht aus dem Volltext.

Konsequenz: Zahlen mit `⚠` sind **zu verifizieren** — am besten, indem du die
Planungsanleitung/Bedienungsanleitung als PDF ins Repo legst oder hochlädst. Dann kann
ich Menüpfade und Parameter exakt statt sinngemäß benennen.

## 1. Was das Gerät physikalisch kann

| Größe | Wert | Anmerkung |
|---|---|---|
| Elektrische Leistung Brennstoffzelle | 750 W | konstant, **nicht modulierend** |
| Thermische Leistung Brennstoffzelle | 1,1 kW | |
| Brennstoffleistung BZ | ≈ 1,97 kW (Hi) | abgeleitet aus 750 W / 38 % |
| El. Wirkungsgrad | ≈ 38 % | ⚠ Hi/Hs-Bezug prüfen |
| Gesamtwirkungsgrad | bis 92 % (Hi) | |
| Spitzenlast-Brennwertmodul | je nach Typ 11,4 / 19,0 / 24,5 / 30,8 kW | F11T/F19T/F25T/F32T |
| Trinkwasserspeicher | 220 l Edelstahl | integriert |
| Standby-Leistungsaufnahme | ≈ 28 W | ⚠ ≈ 245 kWh/a, nicht ignorieren |
| Startvorgang | ≈ 75 min bis 750 W, Reformer-Aufheizung ~800 W Bezug | ⚠ Startenergie ≈ 1–1,5 kWh_el |
| Max. Dauerlauf | 45,5 h, dann 2,5 h Regeneration | ⚠ andere Quelle nennt 120 h — firmware-/typabhängig |
| Max. Tagesertrag | bis 18 kWh_el | |

**Die zwei Eigenschaften, aus denen alles folgt:**

1. **Nicht modulierend.** Die BZ läuft mit 750 W oder gar nicht. Es gibt keine
   Teillast, mit der man auf den Haushaltsverbrauch regeln könnte. Alle Optimierung
   ist deshalb *zeitliche* Optimierung: wann läuft sie, wie lange am Stück.
2. **Teuer im Start, teuer im Takten.** ~75 min Anlauf mit erheblichem Eigenstrombezug.
   Jeder vermiedene Start ist bares Geld. Ziel im Winter ist **ein einziger,
   möglichst langer Block**, nicht viele kurze.

## 2. Betriebsmodi

Aus der Doku ableitbar (⚠ genaue Bezeichnungen je nach Firmware/ViCare-Version):

- **Ökonomisch** — Energiemanager wählt Laufzeit so, dass der Eigenverbrauch des
  erzeugten Stroms maximal wird. Selbstlernend, wertet Lastprofil + Speichertemperatur
  + Vorlauftemperatur aus.
- **Ökologisch** — Priorität CO₂ / möglichst viel Stromproduktion.
- **Energiemanager aus** — rein wärmegeführt: BZ startet abhängig von
  Speichertemperatur und Vorlauftemperatur der Heizkreise.
- **Standby / Aus** — was du im Sommer hattest.

## 3. Die eigentliche Rechnung: Grenzkosten der BZ-kWh

Das ist der Kern. Die BZ lohnt sich **genau dann**, wenn ihre Abwärme tatsächlich
Wärme ersetzt, die sonst die Therme erzeugt hätte. Formal:

```
Grenz-Gasbedarf pro kWh_el  g(u) = (P_gas − u · P_th / η_Kessel) / P_el
                                 = (1,97 − u · 1,1) / 0,75      [η_Kessel ≈ 1,0 Hi]
```

wobei `u` = Anteil der 1,1 kW Abwärme, der wirklich genutzt wird (0 … 1).

| Wärmenutzung u | kWh_Gas je kWh_el | Grenzkosten @ 11 ct/kWh Gas |
|---|---|---|
| 100 % (Winter, Heizung läuft) | 1,16 | **12,8 ct** |
| 75 % | 1,53 | 16,8 ct |
| 50 % (Übergangszeit) | 1,89 | 20,8 ct |
| 25 % | 2,26 | 24,8 ct |
| 0 % (Sommer, Wärme verpufft) | 2,63 | **28,9 ct** |

Dagegen zu halten: Netzbezugspreis (~30–35 ct) bzw. Einspeisevergütung für den
Überschuss (~8 ct + KWK-Zuschlag).

**Daraus folgt direkt, warum deine Sommer-Entscheidung richtig war:** bei u≈0 kostet
die BZ-kWh ungefähr so viel wie Netzstrom, plus Verschleiß, plus 28 W Standby, plus
Startverluste — und die 2 kWp PV mit 4 kWh Akku decken den Sommer-Grundbedarf ohnehin
weitgehend. Standby war korrekt.

**Und ebenso direkt folgt die Winter-Hypothese:** ab dem Moment, wo die Heizung
durchgängig ≥1,1 kW abnimmt, ist u=1 und die BZ-kWh kostet ~13 ct statt ~32 ct
Netzstrom. Dann gilt: **so lange wie möglich am Stück laufen lassen**, und zwar
unabhängig davon, ob der Haushalt gerade 750 W braucht — denn selbst der eingespeiste
Überschuss ist bei u=1 grenzkostenseitig nicht defizitär, sobald KWK-Zuschlag und
Energiesteuerentlastung dazukommen.

Noch nicht in der Tabelle, aber entscheidungsrelevant:
- **KWK-Zuschlag** (Eigenverbrauch vs. Einspeisung, unterschiedliche Sätze) ⚠ prüfen
- **Energiesteuerentlastung** auf das BZ-Gas (§53a EnergieStG), ~0,55 ct/kWh_Gas ⚠
- **Stack-Alterung pro Betriebsstunde** — nur relevant, wenn *kein* Vollwartungsvertrag.
  Mit Vollwartungsvertrag sind die Kosten fix und damit für die Betriebsstrategie
  **irrelevant** (versunkene Kosten). Das ist ein wichtiger Unterschied.

## 4. Die Stellhebel, sortiert nach erwartetem Effekt

### H1 — Wärmesenke dauerhaft offenhalten (größter Hebel)
Die BZ kann nur laufen, wenn 1,1 kW Wärme abgenommen werden. Alles, was den
Rücklauf hochtreibt oder die Wärmeabnahme unterbricht, killt Laufzeit:
- **Nachtabsenkung reduzieren oder streichen.** Kontraintuitiv, aber im BZ-Haus meist
  richtig: eine tiefe Absenkung stoppt nachts die Wärmeabnahme (BZ geht aus oder wird
  ausgebremst) und erzeugt morgens eine Spitze, die die *Therme* deckt. Ein flaches
  Profil hält die BZ durchlaufend.
- **Heizkurve so flach und niedrig wie möglich**, hydraulischer Abgleich, Überström-
  ventile zu. Niedriger Rücklauf = besserer Brennwertbetrieb *und* längere BZ-Laufzeit.
- Einzelraumregelung, die viele Ventile zudreht, ist ein BZ-Killer.

### H2 — Therme aus der BZ-Wärme raushalten
Wenn das Brennwertmodul den 220-l-Speicher auf Temperatur bringt, hat die BZ keine
Senke mehr. Vorrang/Freigabetemperaturen so setzen, dass die Therme nur Spitzenlast
deckt. ⚠ Konkrete Parameter aus der Planungsanleitung nachzuziehen.

### H3 — Regenerationsfenster in die Mittagszeit legen
Die 2,5 h Regeneration (bzw. den Zwangsstopp) auf die Stunden legen, in denen die PV
liefert — im Winter bei 2 kWp allerdings ein kleiner Hebel, im Übergang (Sep/Okt,
März/Apr) ein großer.

### H4 — Akku im Winter als BZ-Puffer statt PV-Puffer umdenken
2 kWp liefern im Dezember ~30–40 kWh/Monat, also praktisch nichts. Der 4-kWh-Akku steht
im Winter leer herum — es sei denn, er darf sich aus dem **BZ-Überschuss** laden
(nachts, wenn der Haushalt <750 W zieht) und morgens/abends in die Lastspitzen
entladen. Das verwandelt eingespeiste 8-ct-kWh in vermiedene 32-ct-kWh.
**Voraussetzung:** der Wechselrichter/EMS muss AC-seitig aus Nicht-PV-Überschuss laden
dürfen. Viele Systeme können das nur eingeschränkt oder gar nicht. → Datenbedarf.

### H5 — Regelkonflikt BZ-Energiemanager ↔ Akku-EMS entschärfen
Beide Regler schauen auf denselben Zählerpunkt und optimieren gegeneinander: Der Akku
deckt die Last → die BZ sieht keinen Bedarf → startet nicht/kürzer. Oder umgekehrt.
Zu klären: Welcher Regler sieht welchen Messpunkt? Gibt es eine Priorisierung? Im
Zweifel im Winter Betriebsmodus auf **wärmegeführt/max. Laufzeit** stellen statt
„ökonomisch" — weil bei u=1 ohnehin *jede* Stunde Laufzeit wirtschaftlich ist und die
Eigenverbrauchsoptimierung des Energiemanagers dann nur schadet.

### H6 — Große Verbraucher umlegen
Im Winter nicht in die (kaum vorhandene) PV-Zeit, sondern in die BZ-Laufzeit.

## 5. Vorläufige Strategie-Hypothese (zu bestätigen mit Daten)

| Zeitraum | Modus | Begründung |
|---|---|---|
| Ab ~15 °C Tagesmittel / Heizgrenze | BZ aus Standby holen, Modus **ökonomisch** | u steigt, aber noch nicht 1 → Eigenverbrauchsoptimierung sinnvoll |
| Kernwinter (durchgehend Heizbetrieb) | Modus **wärmegeführt / max. Laufzeit**, Nachtabsenkung flach, Regeneration mittags | u≈1 → jede Betriebsstunde ~19 ct billiger als Netzbezug |
| Übergang Frühjahr | zurück auf **ökonomisch**, dann Standby | u fällt, Takten vermeiden |
| Sommer | **Standby** (wie gehabt) | bestätigt korrekt |

Die Umschaltschwellen und die Frage „ökonomisch vs. wärmegeführt" lassen sich erst
mit deinen realen Zahlen belegen. Was ich dafür brauche: siehe `02-datenbedarf.md`.
