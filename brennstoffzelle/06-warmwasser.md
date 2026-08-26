# Warmwasser-Strategie

Ist-Zustand (ViCare): Betriebsart Standard · Wunschtemperatur **45 °C** ·
Zeitprogramm **drei Fenster/Tag**, abgelesen ~05:30–08:00, ~11:00–13:30, ~16:30–20:30
(9,0 h Freigabe/Tag) · Zirkulationspumpe und Hygieneprogramm vorhanden.

## 1. Deine Entkopplung läuft bereits richtig

Du hattest berichtet: "Warmwasser wird auf bis 55 °C geheizt, die Gastherme macht max
45 °C." Jetzt sieht man warum — der **Sollwert steht auf 45 °C**, und die 55 °C sind
die Brennstoffzelle, die den Speicher über den Sollwert hinaus lädt, weil ihre Abwärme
irgendwo hin muss.

Das ist genau die Entkopplung, die ich in Dokument 04 empfohlen hatte, und sie ist
bereits da: Die Therme lädt nur bis 45 °C (niedriger Rücklauf, voller Brennwerteffekt),
die letzten 10 K macht die BZ mit ohnehin anfallender Wärme. **Nicht ändern.**

Einzige Ergänzung: In der BZ-Saison die **Maximaltemperatur für die BZ-Wärmeabnahme**
auf 58–60 °C anheben (Fachmann-Ebene, nicht den 45-°C-Sollwert!).

| Ladung bis | nutzbarer Speicherinhalt | entspricht BZ-Laufzeit |
|---|---|---|
| 45 °C | 8,44 kWh | 7,7 h |
| 55 °C | 11,00 kWh | 10,0 h |
| 60 °C | 12,28 kWh | 11,2 h |

Von 55 auf 60 °C sind **+1,2 h Pufferlaufzeit** — gratis, weil die Wärme ohnehin anfällt.

## 2. Die 9-Stunden-Nachtlücke erklärt den Oktober

Aus Dokument 05 war offen, warum die BZ im Oktober nur **53 %** lief, obwohl der
Wärmebedarf (26,9 kWh_th/Tag) für Dauerlauf gereicht hätte. Das Zeitprogramm liefert
die Erklärung:

| Lücke | Dauer |
|---|---|
| **20:30 – 05:30** | **9,0 h** ← über Nacht |
| 08:00 – 11:00 | 3,0 h |
| 13:30 – 16:30 | 3,0 h |

In der Übergangszeit ist der Speicher die einzige verlässliche Wärmesenke — die
Heizung läuft nur sporadisch. Neun Stunden ohne Speicherfreigabe, kombiniert mit
Nachtabsenkung im Heizkreis, heißt: **die BZ verliert nachts ihre Senke, stoppt, und
startet morgens neu.** Das ist genau der eine Start pro Tag, der Oktober, März und
April auf effektive Grenzkosten von 16–17,5 ct treibt statt 14,6 ct.

Im Kernwinter fällt es nicht auf, weil der Heizkreis rund um die Uhr abnimmt — deshalb
dort 92 % Laufzeit trotz identischem Zeitprogramm.

### Empfehlung: saisonales Zeitprogramm

| Saison | Zeitprogramm | Begründung |
|---|---|---|
| **Okt – Apr** (BZ läuft) | **durchgehende Freigabe 00:00–24:00** | Speicher steht als Senke bereit, BZ läuft lange Blöcke statt täglicher Neustarts |
| **Mai – Sep** (BZ Standby) | **die jetzigen drei Fenster behalten** | Therme heizt, jede Stunde Bereitschaft ist reiner Verlust |

Erwarteter Effekt: Oktober von 53 % auf 80–90 %, März von 71 % auf ~90 %.
Zusammen ~350 zusätzliche Betriebsstunden = ~260 kWh Strom, plus ~55 vermiedene Starts.

Wert: bei 16 ct Einspeisung ~25 €/Jahr, bei 8 ct nur ~5 €/Jahr — hängt wieder am
Einspeisetarif. Der vermiedene Startverschleiß am Stack kommt obendrauf und ist bei
fehlendem Wartungsvertrag nicht nebensächlich.

## 3. Der größte Einzelposten: die Zirkulation

Dein gemessener Warmwasserbedarf im Sommer (BZ aus) liegt bei **~10 kWh_th/Tag**.
Das ist für einen kleinen Haushalt viel:

| Posten | kWh_th/Tag |
|---|---|
| Zapfmenge 2 Personen × 40 l auf 45 °C | 3,1 |
| Speicher-Bereitschaftsverlust | ~1,2 |
| **Rest — mutmaßlich Zirkulation** | **~5,7** |

Die Zirkulationspumpe läuft vermutlich mit den drei Warmwasserfenstern mit, also 9 h/Tag.
Bei 5,7 kWh_th/Tag sind das über das Jahr rund **207 m³ Gas ≈ 217 €**.

Die Zahl ist eine Abschätzung — sie steht und fällt mit der Personenzahl und dem
tatsächlichen Zirkulationsprofil. Aber die Größenordnung ist so, dass sie **jeden anderen
Posten in dieser Analyse übertrifft**, inklusive der gesamten BZ-Betriebsoptimierung.

**Zu tun:** Zirkulationsprofil in ViCare öffnen und auf zwei kurze Fenster stutzen
(z. B. 06:30–08:00 und 18:00–20:00), oder besser auf Impuls-/Bedarfssteuerung umstellen.
Realistisch 3–4 kWh_th/Tag sparbar = **110–150 €/Jahr**.

### Wichtig: nicht als BZ-Wärmesenke rechtfertigen

Man könnte argumentieren, die Zirkulationsverluste seien nützlich, weil sie der BZ eine
Senke verschaffen. Das ist falsch:

| Verwertung der BZ-Stunde | Erlös | Ergebnis je Betriebsstunde |
|---|---|---|
| Strom 100 % eigenverbraucht | 23,2 ct | **+1,0 ct** |
| Strom 100 % eingespeist @ 16 ct | 12,0 ct | −10,3 ct |
| Strom 100 % eingespeist @ 8 ct | 6,0 ct | −16,3 ct |

Eine BZ-Betriebsstunde kostet 22,3 ct Gas. Wenn die Wärme wertlos verpufft, trägt sich
das selbst im besten Fall gerade eben. **Wärme künstlich zu erzeugen, damit die BZ
läuft, lohnt nie.** Zirkulation kürzen, auch wenn dadurch die BZ-Laufzeit sinkt.

## 4. Hygieneprogramm — genau dann wichtig, wenn die BZ aus ist

45 °C Speichertemperatur liegt im Legionellen-Wachstumsbereich. In der BZ-Saison ist
das entschärft, weil die Brennstoffzelle den Speicher regelmäßig auf 55 °C durchheizt.

**Von Mai bis September fehlt genau diese Durchheizung** — fünf Monate mit einem 220-l-
Speicher konstant auf 45 °C. Das ist die kritische Phase.

Zu prüfen: Ist das Hygieneprogramm aktiv, auf welche Temperatur und in welchem Intervall?
Empfehlung: wöchentlich auf ≥ 60 °C, mindestens in den Standby-Monaten. Das kostet
~0,6 kWh_th pro Durchlauf, also praktisch nichts.

Wenn die Zirkulation gekürzt wird, gewinnt dieser Punkt zusätzlich an Gewicht — eine
selten durchspülte Zirkulationsleitung auf 45 °C ist der ungünstigste Fall.

## 5. Zusammenfassung Warmwasser

| Maßnahme | Wann | Wert |
|---|---|---|
| **Zirkulation auf 2 kurze Fenster / Bedarfssteuerung** | sofort, ganzjährig | **110–150 €/a** |
| Zeitprogramm Okt–Apr auf Dauerfreigabe | zur BZ-Saison | 5–25 €/a + Stackschonung |
| Zeitprogramm Mai–Sep: drei Fenster behalten | jetzt | bereits richtig |
| BZ-Maximaltemperatur auf 58–60 °C | Fachmann-Ebene | +1,2 h Puffer je Zyklus |
| Sollwert 45 °C unverändert lassen | — | Entkopplung funktioniert |
| Hygieneprogramm ≥ 60 °C wöchentlich prüfen | vor Mai | Hygiene, ~0 Kosten |
