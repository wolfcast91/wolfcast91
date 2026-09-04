# Monetarisierungskonzept — Season 1 → 30.000-€-Ziel

Ergänzt [`REGELWERK.md`](./REGELWERK.md) (siehe dort §11) und
[`SKRIPTE.md`](./SKRIPTE.md). Beantwortet: *maximale Monetarisierung ab
Post 1, ohne zu stören.*

## 1. Grundprinzip: der Kreislauf

```
Zuschauer kauft über Affiliate-Link (Werkzeug/Ersatzteil)
  → Provision fließt sichtbar in den "Projekt-Fonds"
    → Fonds beschleunigt den Build UND finanziert den nächsten Giveaway
      → größere Reichweite, mehr Käufe
        → Fonds wächst weiter
```

Jeder Kauf ist damit sichtbar Teil der Geschichte — nicht Werbe­unterbrechung.
Die Formel dafür ist bereits in eurem Motto vorgegeben: *"Du willst
mitbauen? Hier gibt's Ersatzteile, Werkzeug — damit ich das Projekt
schneller voranbringen kann. Und du das Traumauto gewinnst."* Der
Zuschauer kauft nicht *von* euch, er hilft *sich selbst* zu einer
größeren Gewinnchance.

**Wichtig für "maximal, ohne zu stören":** *maximal* heißt hier
**Flächen­abdeckung**, nicht **In-Video-Frequenz**. Die Beschreibung, der
Pinned Comment, die Kanal-Info und der Link in Bio haben unbegrenzt
Platz für die volle Liste — das Video selbst bekommt genau **einen**
kurzen, kontextuellen Moment. Maximale Monetarisierung entsteht durch
Wiederholung über alle Flächen hinweg, nicht durch mehr Werbung im Bild.

## 2. Warum das zu den sechs Gefühlen passt

(Gefühle: cinematisch, bodenständig, ruhig, witzig, fleißig, naiv —
siehe Regelwerk §1a)

| Gefühl | Wie die Monetarisierung es einhält |
|---|---|
| Bodenständig / naiv | Nur Dinge bewerben, die tatsächlich benutzt werden — kein Fake-Sponsoring, keine Fremdprodukte |
| Fleißig | Der Fonds-Stand ist ein sichtbarer Fortschrittszähler, genau wie Tage/Stunden im `MonoReadout` |
| Witzig | Die Einladung bleibt informell ("Willst du mitbauen?"), nie Verkaufsdruck |
| Ruhig / cinematisch | Platzierung ist selten und kontextuell, nie im Hook oder im Turn-Satz-Moment |

## 3. Placement-Regeln — das "ohne zu stören"

1. **Maximal ein sichtbarer Affiliate-Moment pro Video.**
2. **Nie im Cold-Open-Hook, nie im Turn-Satz.** Diese beiden Momente
   bleiben komplett unkommerziell — sie tragen die Emotion des Posts
   (Regelwerk §6) und dürfen nicht mit Verkauf verknüpft werden.
3. **Immer kontextuell**, direkt an eine Szene angedockt, in der das
   Werkzeug/Teil gerade tatsächlich gebraucht wurde. Kein generischer
   "Sponsor dieses Videos"-Break. Beispiel Post 1: Szene 2
   (Ölpeilstab-Problem) ist der natürliche Platz — direkt danach ein
   kurzer Callout zum passenden Werkzeug.
4. **Visuelle Form:** kleine Season-Familie-Komponente, keine neue
   Bildsprache — `MarkerLine`-Caption-Stil, unten platziert, ~3–4 s
   eingeblendet, optional mit `MonoReadout` für einen Rabattcode.
5. **Sprache:** immer einladend ("Willst du mitbauen? Link unten."),
   nie imperativ ("Jetzt kaufen!", "Nur heute!"). Keine künstliche
   Dringlichkeit — widerspricht "ruhig/bodenständig".
6. **Vollständige Liste** (alle Teile, alle Links) immer in
   Beschreibung + Pinned Comment + Link in Bio. Das Video teasert nur.

## 4. Der Fonds als wiederkehrendes Motiv

Neue Season-Komponente (Vorschlag, siehe §7): ein `ProjektFonds`-Stempel
im selben Stil wie der `DayOne`-Stempel, aber mit Euro-Betrag statt
Tage/Stunden — z. B. *"PROJEKT-FONDS: 1.240 € — schneller ans Ziel."*
Erscheint **einmal pro Video, im Outro**, nie im Cold Open. Macht die
Monetarisierung Teil der Erzählung: Der Zuschauer sieht direkt, dass
sein Kauf etwas bewegt hat.

## 5. Phasen-Fahrplan

| Phase | Wann | Was |
|---|---|---|
| **1 — Sofort** | ab Post 1 | Affiliate-Links (z. B. Amazon-Partnerprogramm, Kfz-Teile-Partnerprogramme) auf alles, was im Video real benutzt wird. Volle Ausstattungsliste in jeder Beschreibung. Ein Callout pro Video. Kein Sponsoring, nur Affiliate — glaubwürdig von Tag 1. |
| **2 — Nach Reichweite** | sobald Zahlen belastbar sind (Richtwert: ~10 Posts) | Direktverhandlung mit Werkzeug-/Teile-Händlern: bessere Provisionen, personalisierte Rabattcodes (z. B. `TRAUMAUTO10`) — bessere Konditionen für Zuschauer *und* höhere Marge. Sichtbarkeitsregeln bleiben identisch. |
| **3 — Season-Finale** | Übergabe des Traumautos | Fonds-Reveal zeigt die kumulierte Wirkung der Community-Käufe — direkte Kausalkette zum Giveaway. Cliffhanger: *"Deshalb kann ich jetzt schon sagen: Season 2 verschenke ich 30.000 €."* |
| **4 — Season 2** | ab 30.000-€-Kampagne | Gleiche Mechanik, jetzt mit belegbarer Reichweite für größere Partnerschaften / Umsatzbeteiligungen statt reiner Klick-Provision. |

## 6. Tracking & Transparenz

- Jeder Post bekommt einen eigenen UTM-Parameter bzw. Rabattcode →
  Erfolg pro Post ist messbar (optionale zusätzliche Spalte
  "Affiliate-Code" in der Status-Tabelle von `SKRIPTE.md`).
- In regelmäßigen Abständen (Vorschlag: jeder 10. Post oder bei
  Meilensteinen) ein kurzer eigener "Fonds-Stand"-Beat — Transparenz
  erhöht Vertrauen, Vertrauen erhöht Klickrate. Die ehrliche
  Grundhaltung des Kanals wird so zum Verkaufsargument statt zum
  Widerspruch.

## 7. Technische To-dos (neue Komponenten)

- **`AffiliateCallout`** — kurze, transparente Caption im
  `MarkerLine`-Stil. Kann dieselbe Basis wie die in Post 1 ohnehin
  benötigte Caption-Overlay-Komponente nutzen (siehe Regelwerk §2a) —
  beide sollten aus derselben Komponente gebaut werden, nicht doppelt.
- **`ProjektFonds`** — Outro-Stempel, `MonoReadout`-basiert wie der
  `DayOne`-Stempel, aber mit €-Betrag statt Tag/Stunden.

## 8. Rote Linien — was nicht passiert

- Keine Erwähnung im Hook oder im Turn-Satz.
- Keine Fremdprodukt-Platzierungen — nur, was tatsächlich benutzt wird.
- Kein Kauf-Imperativ, keine künstliche Verknappung.
- Keine ungekennzeichnete Werbung (siehe §9).
- Nie mehr als ein sichtbarer Callout pro Video — Ausnahmen brauchen
  eine bewusste Entscheidung, keine stille Häufung.

## 9. Rechtlicher Hinweis (keine Rechtsberatung)

Affiliate-Links müssen in Deutschland als Werbung gekennzeichnet werden
(Kennzeichnungspflicht für kommerzielle Kommunikation, u. a. § 5a UWG).
In der Praxis reicht meist ein klarer Hinweis in der Beschreibung
(*"Mit \* markierte Links sind Affiliate-Links"*) plus eine kurze
mündliche/visuelle Kennzeichnung beim Callout selbst. Bei Kooperationen
ab Phase 2 (Rabattcodes, Verhandlungen mit Händlern) empfiehlt sich
eine kurze anwaltliche Prüfung — dieses Dokument ersetzt das nicht.
