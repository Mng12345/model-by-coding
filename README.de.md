[English](README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · Deutsch

> Dies ist die deutsche Übersetzung von README.md; bei Abweichungen gilt die englische Fassung.

# model-by-coding

Ein Agent Skill: ein reales Objekt aus Fotos als deterministisches three.js-Modell nachbauen und daraus einen Zerlegungsfilm und ein GIF machen – ohne 3D-Modellierungssoftware zu öffnen.

Dieses Repository ist der Skill selbst: Anweisungen, denen ein Agent folgen kann, wiederverwendbare Skripte, ausführliche Referenznotizen und ein vollständiges Beispiel – ein weißer USB-Schreibtischventilator, in Code nachgebaut und als Film mit 13 Teilen, 1920×1080, 30 fps und 43,5 Sekunden gerendert.

- [Was das ist](#was-das-ist)
- [Welches Problem es löst](#welches-problem-es-löst)
- [Die vierstufige Pipeline](#die-vierstufige-pipeline)
- [Schnellstart](#schnellstart)
- [Repository-Aufbau](#repository-aufbau)
- [Skripte](#skripte)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Lizenz](#lizenz)
- [Danksagung und Links](#danksagung-und-links)

## Was das ist

Ein Agent Skill ist ein Verzeichnis, das ein Agent lädt: ein `SKILL.md`-Einstiegspunkt plus die Notizen und Skripte, die eine Aufgabe braucht. Dieses Repository besteht aus vier Teilen:

| Teil | Inhalt |
| --- | --- |
| `SKILL.md` | Der Einstiegspunkt: wann der Skill greift, die Pipeline selbst und die nicht verhandelbaren Regeln. |
| `references/` | Sechs ausführliche Notizen für Details, die nicht in die Skill-Datei passen: Modellierung, Rendering, Verifikation, GIF-Export, Veröffentlichung und eine Sammlung von Fallstricken. |
| `scripts/` | Wiederverwendbare Werkzeuge: ein Einzelbild-Viewer, ein Vergleichsbogen Foto gegen Rendering, ein Leser für die Check-Ausgabe und eine GIF-Bedienkarte. |
| `examples/fan/` | Das vollständige Beispiel: Fotos, Modellquelltext, HyperFrames-Projekt, Verifikationsrenderings und Ergebnisse. |

Das Beispiel ist kein Mockup. Die Fotos hat der Autor selbst aufgenommen, das Modell ist handgeschriebenes JavaScript, der Film wurde aus diesem Modell gerendert, und der Vergleichsbogen mit sechs Winkeln liegt im Repository. Zusammen zeigen sie, was herauskommt, wenn man die Anleitung von Anfang bis Ende befolgt. Die Zahlen stehen in [examples/fan/README.md](examples/fan/README.md) – einschließlich der Abweichungen, die nicht korrigiert wurden.

Zuerst `SKILL.md` lesen. Die Referenzen sind der Teil, der mehr Platz braucht:

| Datei | Thema |
| --- | --- |
| `references/01-modeling.md` | Koordinatensystem, gemessene Verhältnisse, Rotationsprofile, Gitter- und Blattparameter, Anker pro Teil. |
| `references/02-render.md` | Der Rendering-Vertrag von HyperFrames, die Einstellungsliste, die Audio-Synchronpunkte. |
| `references/03-verify.md` | Headless-Aufnahmen, Bounding-Box-Vergleich, Prüfung pro Winkel und das gescheiterte Overlay-Experiment. |
| `references/04-gif.md` | Die Schritt-für-Schritt-Karte für gif-master, Credit-Grenzen und der ffmpeg-Ersatzweg. |
| `references/05-publish.md` | Veröffentlichungs-Checkliste und die praktischen Hürden der üblichen Ziele. |
| `references/06-gotchas.md` | Unter anderem: Tonemapping und Belichtung, Lichtabfall, Schattenbanding, Gitterstäbe, die flache Bänder statt runder Rohre sein müssen, Mindesttextgröße und eingecheckte `.min.js`-Dateien. |

## Welches Problem es löst

Auf die Bitte „mach ein 3D-Modell von diesem Objekt“ liefert ein Agent meist eines von zwei Dingen: ein hübsches Rendering, das niemand prüfen kann, oder ein Mesh mit willkürlichen Proportionen, mit dem sich kein Film bauen lässt. Beides ist schwer zu reviewen. Die Kameraposition eines Renderings ist normalerweise unbekannt, also lässt es sich nicht neben das Foto legen, und nach einer Änderung lässt sich das Asset nicht neu ableiten.

Dieser Skill ersetzt das durch eine Schleife, in der jeder Schritt Belege hinterlässt.

1. **Verhältnisse werden gemessen, nicht geraten.** Jede Konstante im Modell lässt sich entweder auf eine Messung im Foto zurückführen oder ist als Schätzung markiert. Weitergegeben werden Verhältnisse, keine absoluten Maße.
2. **Derselbe Frame ist reproduzierbar.** Das Modell gibt nur einfachen Zustand preis – Kameraposition, Explosionsgrad, Blattwinkel – und sonst nichts. Keine Uhr, kein Zufall, kein Netzwerk. Gleiche Eingabe, gleicher Frame, also kann das Review eine exakte Kameraposition adressieren.
3. **Der Vergleich läuft unter gleichen Bedingungen.** Jedes Rendering wird aus der Kameraposition des Referenzfotos aufgenommen, beide Seiten werden auf ihre eigene Silhouetten-Bounding-Box zugeschnitten und auf dieselbe Kachel skaliert. Bildausschnitt und Abstand können Proportionsfehler nicht mehr verdecken.
4. **Ein Modell versorgt alle Ergebnisse.** Dasselbe Bundle treibt die Verifikations-Standbilder, die interaktive Seite und den Film. Ein Fix am Modell erreicht alle.
5. **Ergebnisse sind mit git reviewbar.** Das Modell ist Code und benannte Konstanten. Änderungen sind Diffs, keine Binärassets.

Es ist nicht:

- Photogrammetrie oder ein 3D-Scanner – Geometrie wird nicht automatisch rekonstruiert;
- CAD – die Maße sind Verhältnisse aus Fotos, keine Messungen am realen Objekt;
- ein Blender-Ersatz oder ein allgemeines Modellierungswerkzeug;
- ein gehosteter Dienst, und es enthält keine Modellgewichte.

## Die vierstufige Pipeline

Jeder Schritt erzeugt das Ergebnis, das der nächste braucht. Die Reihenfolge unten fasst das Messen in Schritt 1 zusammen; `SKILL.md` führt es als eigenen Schritt, und das Beispiel begann mit der Verifikation schon früh in der Modellierungsphase und wiederholte den Check während der Filmarbeit.

### Schritt 1: Aus den Fotos in Code modellieren

Eingabe: ein frontales Foto plus alle brauchbaren Zusatzwinkel. Das Beispiel nutzt sechs: eine frontale Dreiviertelansicht und fünf Winkelaufnahmen (side-left, back, back three-quarter, bottom, top).

Was der Agent tut:

- Das Foto vermessen. Im Beispiel bestimmt ein Radialscan der Außenkante den Kopfkreis und seinen Mittelpunkt, die Winkelperiode bei festem Radius liefert die Zahl der Gitterstäbe, und Verhältnisse ergeben Kopfdicke, Durchmesser der Mittelkappe, Sockeldurchmesser und Drehknopfdurchmesser.
- Einen Weltmaßstab wählen und als Annahme deklarieren. Das Beispiel setzt 190 mm Kopfdurchmesser und leitet alles andere als Verhältnis davon ab.
- Geometrie aus three.js-Primitiven und Rotationsprofilen bauen: Ringe, Streben, Blätter, Motorzylinder, Gitterstäbe, Sockelteile. Die Teile sind eigene benannte Objekte, weil der Film sie einzeln bewegt.
- Jedem Teil einen Explosions-Offset und einen Anker im Bildschirmraum für sein Leader-Label geben.
- Die API zeitfrei halten: `setView()`, `setExplode()`, `setSpin()`, `render()`, `getAnchors()`. Kein `Date.now()`, kein `requestAnimationFrame`, keine Netzwerkanfrage.
- Szene und three.js mit esbuild zu einem IIFE bündeln, das Seite, Viewer und Film laden.
- Branding entfernen. Die beschrifteten Flächen des Modells bleiben leer; Marken- und Typenschilder auf den Referenzfotos wurden aus demselben Grund unscharf gemacht.

Ausgabe: `examples/fan/src/fan-scene.js` und das gebaute `examples/fan/video/assets/vendor/fan.bundle.min.js`.

### Schritt 2: Den Zerlegungsfilm mit HyperFrames rendern

[HyperFrames](https://github.com/heygen-com/hyperframes) macht aus einer HTML-Seite ein Video, indem es eine pausierte Timeline treibt und Frame für Frame aufnimmt.

- `examples/fan/video/index.html` ist die Kompositionswurzel: `data-duration="43.5"`, 1920×1080.
- Die pausierte GSAP-Timeline ist unter `window.__timelines.main` registriert. Die Seite hört auf `hf-seek` und zeichnet das Canvas aus `event.detail.time` neu; nichts läuft von selbst weiter, also lässt sich jeder Frame aufnehmen.
- Das Beispiel mit 43,5 Sekunden hat zehn Einstellungen: Titel, Orbit, Gitter-Makro, hinteres Dreiviertel, Naben-Makro, Weitwinkel, Explosion, Standbild mit 13 Leader-Labels, Zusammenbau, Endcard.
- Die Explosion ist ein Fortschrittswert pro Teil. Die Trennung beginnt bei 21,15 s in 0,30-s-Schritten; der Zusammenbau beginnt bei 35,18 s in 0,25-s-Schritten; das letzte Teil rastet bei 38,45 s ein. Jedes Leader-Label beginnt 0,30 s nach dem Start seines Teils einzublenden (der Fade selbst dauert 0,45 s).
- Der Ton wird nach demselben Vertrag geschnitten. Der Mix des Beispiels ist 43,5 s lang, 48 kHz, 16-Bit-Stereo, mit −16,0 LUFS integrierter Loudness und −2,0 dBTP True Peak. `examples/fan/video/assets/audio/sources.md` listet Quellen und Bearbeitungskette.
- `check` ist das Gate: vor dem Rendern muss der Bericht null Probleme melden. `snapshot --at <Sekunden>` nimmt einen einzelnen Frame zur Kontrolle auf; das Poster des Beispiels ist der Frame bei 27,6 s.

Ausgabe: eine MP4-Datei unter `examples/fan/video/renders/`, standardmäßig benannt `video_<YYYY-MM-DD>_<HH-MM-SS>.mp4`.

### Schritt 3: Gegen die Fotos verifizieren

Diese Prüfung ist ein Vergleich aus derselben Kamera, kein Eindruck.

1. Mit Headless-Chrome aus der Kameraposition des Referenzfotos aufnehmen. `scripts/view.html` liest die Position aus URL-Query-Parametern (`yaw`, `pitch`, `dist`, `tx`, `ty`, `tz`, `fov`) und rendert einen Frame in 1920×1080. Es gibt keine Animationsschleife, und die Seite stellt selbst keine Netzwerkanfragen.
2. Das Foto auf den von Hand gelesenen Rahmen zuschneiden, das Rendering auf seine eigene Bounding Box. Im Beispiel wird der Fotorahmen aus einem Raster-Overlay gelesen, die Rendering-Box aus den projizierten Außenkanten von Kopf und Sockel berechnet. `scripts/verify_sheet.py` kann die Rendering-Box auch über die Hintergrundfarbe automatisch finden.
3. Beide Zuschnitte auf dieselbe Kachel skalieren und nebeneinander legen. Bildausschnitt und Abstand sind normalisiert, also lassen sich Kopfdicke, Durchmesser der Mittelkappe, Zahl der Gitterstäbe und Sockelbreite direkt vergleichen.
4. Jeden Winkel prüfen, Abweichungen notieren, die gemessenen Konstanten anpassen, neu rendern und wiederholen.

Der Vergleichsbogen des Beispiels hat sechs Zeilen. Das dokumentierte Ergebnis ist eine enge Übereinstimmung mit sieben bekannten Abweichungen, darunter die Höhe der Kopfmitte (1,02 D im Modell, 1,04–1,10 D auf den Fotos), ein etwas breiterer Außenring des hinteren Gitters und ein um einige Prozent zu großes Bedienfeld. Diese Abweichungen stehen in den Notizen des Beispiels, statt versteckt zu werden.

Das Verfahren hält auch ein negatives Ergebnis fest. Der frühe Plan war ein 50/50-Overlay aus derselben Kamera, mit Kreis-Fit und Normalisierung des Kopfkreises. Zuerst wurde über fünf Fotos ein Kreis gefittet; bei vier davon gehörten die stärksten gekrümmten Kanten zum Hintergrund, die normalisierten Radien waren damit unbrauchbar. Nur das Frontfoto, in dem das Objekt vor einer gleichmäßigen Wand das Bild füllt, lieferte einen brauchbaren Radialscan. Das Overlay wurde verworfen, der Bounding-Box-Vergleich ersetzte es; die Begründung steht in `references/03-verify.md`.

Dieser Schritt ist eine Sichtprüfung mit ausdrücklichen Bounding Boxes, kein numerisches Zertifikat.

### Schritt 4: Das GIF exportieren

Der letzte Schritt ist manuell, weil er im Browser läuft:

1. Das Werkzeug öffnen: [Video zu GIF (Englisch)](https://gif-master.com/en/tools/video-to-gif) oder [Video zu GIF (Chinesisch)](https://gif-master.com/zh/tools/video-to-gif).
2. Die gerenderte MP4 hineinlegen. Die Datei wird im Browser verarbeitet und nicht hochgeladen.
3. Auf eine Bewegung zuschneiden – eine Explosion oder eine Makroaufnahme statt des ganzen 43,5-s-Films –, Framerate und Größe setzen, Vorschau ansehen.
4. Exportieren. Bearbeiten ist kostenlos; der Download verlangt Anmeldung, das kostenlose Kontingent sind 3 Credits pro Tag.

`references/04-gif.md` fasst dieselben Schritte als Checkliste zusammen und beschreibt einen lokalen ffmpeg-Ersatzweg.

### Die Ergebnisse in Reihenfolge

```
examples/fan/
├─ reference/fan.jpg, reference/angles/*.jpg    input: six photographs
├─ src/fan-scene.js                             step 1: model, materials, camera, anchors
├─ video/assets/vendor/fan.bundle.min.js        step 1: the bundle every consumer loads
├─ video/index.html, video/assets/director.js   step 2: composition and timeline
├─ video/assets/audio/mix.wav                   step 2: Release asset, not in git
├─ video/renders/*.mp4                          step 2: output, git-ignored
├─ out/verify2/*-render.png                     step 3: same-camera stills
├─ out/review-sheet.png                         step 3: six photo-versus-model pairs
├─ out/poster.png                               deliverable: 1920×1080 teardown still
└─ out/contact-sheet.png                        deliverable: 4×3 contact sheet
```

## Schnellstart

### Voraussetzungen

| Voraussetzung | Zweck |
| --- | --- |
| Node.js 22 (getestet mit 22.19.0) | Führt die HyperFrames-CLI und esbuild über `npx` aus. |
| Python 3.11 mit Pillow | `scripts/verify_sheet.py` (numpy optional); `examples/fan/tools/review_sheet.py` braucht numpy; die Audio-Rebuild-Skripte des Beispiels brauchen numpy und scipy. |
| ffmpeg | HyperFrames-Rendering und die Audio-Arbeit im Beispiel. |
| Chrome oder Chromium | Headless-Aufnahmen und die Frame-Erfassung von HyperFrames. |
| HyperFrames CLI 0.9.36 | Wird über `npx --yes hyperframes@0.9.36` geholt; keine globale Installation nötig. |
| git | Klonen von Skill und Beispiel. |

`scripts/hf_read_check.py` nutzt nur die Python-Standardbibliothek. `scripts/view.html` braucht nur einen Browser und das gebaute Modell-Bundle.

### Den Skill installieren

Das Repository in ein Skill-Verzeichnis klonen. Projektlokal folgt der Skill dem Projekt, das ihn nutzt; benutzerweit steht er allen Projekten zur Verfügung.

```bash
# project-local
git clone https://github.com/Mng12345/model-by-coding.git .agents/skills/model-by-coding

# or user-wide
git clone https://github.com/Mng12345/model-by-coding.git ~/.agents/skills/model-by-coding
```

Agenten wie DeepSeek Harness und Claude Code lesen Skills aus `.agents/skills/` im Projekt oder aus `~/.agents/skills/` beim Nutzer.

Wenn eine skills-CLI vorhanden ist, genügt für dieselbe Installation ein Befehl:

```bash
npx skills add Mng12345/model-by-coding
```

Danach eine neue Agent-Session öffnen und den Skill in der Anfrage nennen (`model-by-coding`). Wie er aufgerufen wird, hängt vom Client ab.

### Den Beispielfilm rendern

Das Repository enthält kein binäres Audio. `mix.wav` aus dem [neuesten Release](https://github.com/Mng12345/model-by-coding/releases/latest) herunterladen und vor dem Check an seinen Platz zurücklegen.

```bash
# 1. put the mixed track back (asset name: mix.wav)
curl -L -o examples/fan/video/assets/audio/mix.wav \
  https://github.com/Mng12345/model-by-coding/releases/latest/download/mix.wav

# 2. check the HyperFrames project, then render
cd examples/fan/video
npx --yes hyperframes@0.9.36 check
npx --yes hyperframes@0.9.36 render --quality delivery
```

`check` muss null Probleme melden, bevor gerendert wird. Das Ergebnis landet in `examples/fan/video/renders/video_<YYYY-MM-DD>_<HH-MM-SS>.mp4`; die CLI benennt die Datei nach dem Projektverzeichnis und der Renderzeit. Wenn eine lokale Vorschau im Browser nützlich ist, vor dem Rendern `preview` aufrufen:

```bash
npx --yes hyperframes@0.9.36 preview
```

Um einen einzelnen Moment statt des ganzen Films zu prüfen:

```bash
npx --yes hyperframes@0.9.36 snapshot --at 27.6
```

Snapshots werden im Verzeichnis `.hyperframes/artifacts/snapshots/` des Projekts abgelegt.

Die eingecheckten Standbilder in `examples/fan/out/` – Poster, 4×3-Kontaktbogen, Vergleichsbogen mit sechs Winkeln und die sechs Winkelrenderings – lassen sich ohne jedes Rendering ansehen.

## Repository-Aufbau

```
model-by-coding/
├─ SKILL.md                          skill entry point
├─ README.md                         this file
├─ README.zh-CN.md                   Simplified Chinese translation
├─ README.zh-TW.md                   Traditional Chinese translation
├─ README.ja.md                      Japanese translation
├─ README.de.md                      German translation
├─ README-LICENSES.md                license scope, attribution format, third-party assets
├─ LICENSE                           MIT, with the media exception noted at the end
├─ references/
│  ├─ 01-modeling.md
│  ├─ 02-render.md
│  ├─ 03-verify.md
│  ├─ 04-gif.md
│  ├─ 05-publish.md
│  └─ 06-gotchas.md
├─ scripts/
│  ├─ view.html                      single-frame viewer driven by URL query
│  ├─ verify_sheet.py                photo-versus-render comparison sheet
│  ├─ hf_read_check.py               reads the JSON form of a HyperFrames check
│  └─ make_gif.md                    gif-master operation card (documentation)
└─ examples/
   └─ fan/                           worked example; see examples/fan/README.md
      ├─ README.md                   the example's own notes, measurements and deviations
      ├─ src/
      │  ├─ fan-scene.js             geometry, materials, lighting, anchors
      │  ├─ director.js              camera moves and timeline for the film
      │  └─ fan-ui.js                inspection UI for the standalone HTML build
      ├─ video/
      │  ├─ index.html               composition root, 43.5 s
      │  ├─ hyperframes.json         HyperFrames project configuration
      │  ├─ meta.json                project id and name
      │  ├─ package.json             npx shortcuts for preview (dev), check, snapshot, render
      │  └─ assets/
      │     ├─ director.js           the director compiled for the film
      │     ├─ fonts/                Inter and Inter Tight woff2, with OFL license texts
      │     ├─ vendor/               fan.bundle.min.js and gsap.min.js
      │     └─ audio/
      │        ├─ sources.md         soundtrack sources, processing chain, measured levels
      │        └─ work/              synthesis, mixing, mastering and verification scripts
      ├─ reference/
      │  ├─ fan.jpg                  front three-quarter photograph
      │  └─ angles/                  five additional angles (side-left, back, back 3/4, bottom, top)
      ├─ tools/
      │  ├─ review_sheet.py          builds out/review-sheet.png; runs as-is
      │  ├─ grid6.py                 historical one-off measurement script
      │  ├─ measure-photo.py         historical one-off measurement script
      │  └─ expo_check.py            historical one-off measurement script
      └─ out/
         ├─ poster.png               1920×1080 teardown still
         ├─ contact-sheet.png        4×3 contact sheet of the film
         ├─ review-sheet.png         six photo-versus-model pairs
         └─ verify2/                 six per-angle renders, 1920×1080 each
```

## Skripte

| Pfad | Art | Funktion |
| --- | --- | --- |
| `scripts/view.html` | Browserseite | Rendert einen Frame eines in Code gebauten Modells aus der Kameraposition in der URL. Parameter: `bundle`, `global`, `yaw`, `pitch`, `dist`, `tx`, `ty`, `tz`, `fov`, `explode`, `spin`, `tilt`, `lift`, `w`, `h`, `dpr`, `bg`; die Debug-Flags pro Teil `noshadow`, `hide` und `only` werden an das Bundle durchgereicht. |
| `scripts/verify_sheet.py` | Python | Schneidet ein Foto und ein Rendering auf ihre eigenen Bounding Boxes, skaliert beide auf dieselbe Kachel und schreibt ein Vergleichsbild nebeneinander. Pflicht: `--photo`, `--render`, `--out` und eine von Hand gelesene `--bbox x0,y0,x1,y1`; optional `--render-bbox` (standardmäßig aus der Hintergrundfarbe erkannt), `--bg`, `--threshold`, `--pad` (Standard `0.04`), `--tile` (Standard `520x620`), `--gap`, `--label-height`, `--label-photo`, `--label-render`. Pillow ist Pflicht, numpy beschleunigt nur die Hintergrundmaske. |
| `scripts/hf_read_check.py` | Python | Liest einen HyperFrames-Check-Bericht – entweder das JSON, das `check --json` ausgibt, oder das Artefakt, das HyperFrames unter `.hyperframes/artifacts/checks/` speichert – und gibt `ok` plus die Befundzahlen pro Abschnitt aus (lint, runtime, layout, motion, contrast, craft, audio). `--max` begrenzt die ausgegebenen Befunde, `--json` gibt die Zusammenfassung als JSON aus, `--fail-on-error` beendet mit Fehlercode, wenn der Bericht fehlgeschlagen ist. Nur Standardbibliothek; akzeptiert UTF-8- und UTF-16-Berichte. |
| `scripts/make_gif.md` | Dokumentation | Die Bedienkarte für gif-master: Schritte, Grenzen und der lokale ffmpeg-Ersatzweg. Nicht ausführbar. |

Der Viewer lädt das in der Query genannte Bundle. Das mitgelieferte Beispiel-Bundle ist ein einfaches IIFE, also lässt sich die Kamera direkt setzen:

```
file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30
```

Aufnahme mit Headless-Chrome in derselben Größe:

```bash
chrome --headless=new --hide-scrollbars --window-size=1920,1080 \
  --screenshot=front.png \
  "file:///<path-to-repo>/scripts/view.html?bundle=../examples/fan/video/assets/vendor/fan.bundle.min.js&yaw=-10&pitch=12&dist=0.85&ty=0.185&fov=30"
```

Einen Vergleichsbogen aus den eingecheckten Renderings des Beispiels bauen:

```bash
python scripts/verify_sheet.py \
  --photo examples/fan/reference/fan.jpg \
  --render examples/fan/out/verify2/front-render.png \
  --bbox 130,245,1195,1455 \
  --out front-pair.png
```

Einen gespeicherten Check-Bericht lesen. HyperFrames legt seine Kopie unter `.hyperframes/artifacts/checks/<uuid>.json` ab; das Skript akzeptiert auch einen von stdout umgeleiteten Bericht:

```bash
cd examples/fan/video
npx --yes hyperframes@0.9.36 check --json > check.json
python ../../../scripts/hf_read_check.py check.json

# or point it at the report the CLI saved itself
python ../../../scripts/hf_read_check.py .hyperframes/artifacts/checks/<uuid>.json
```

Die Werkzeuge in `scripts/` sind parametrisiert: keine Objektnamen, keine ventilatorspezifischen Pfade, keine absoluten Pfade. Die vier Skripte in `examples/fan/tools/` sind die, die in der Fallstudie tatsächlich benutzt wurden. `review_sheet.py` arbeitet mit relativen Pfaden und läuft im Repository unverändert; `grid6.py`, `measure-photo.py` und `expo_check.py` bleiben als Prozessdokumentation erhalten, und ihr Dateikopf sagt, dass ihre Eingaben nicht Teil dieses Repositories sind – sie laufen also nicht unverändert.

## Bekannte Einschränkungen

- **Verhältnisse, keine zertifizierten Maße.** Das Beispiel setzt 190 mm Kopfdurchmesser als deklarierte Annahme für den absoluten Maßstab, weil in den Fotos kein Maßstab steckt. Alle anderen Maße sind Verhältnisse dazu. Das Modell ist kein Messgerät.
- **Verdeckte Flächen sind geschätzt.** Details des hinteren Gitters, der Motorinnenraum, die Klapphaken-Mechanik und Teile des Sockels sind auf den Fotos nicht vollständig sichtbar. In den Notizen sind sie als Schätzung markiert und sollten nicht als gesicherte Fakten über das reale Produkt gelesen werden.
- **Die Verifikation ist visuell.** Die Bounding-Box-Ausrichtung entfernt Unterschiede im Bildausschnitt, aber der Fotorahmen wird von Hand gelesen, und es gibt keinen numerischen Schwellenwert, den ein Ergebnis bestehen muss. Der Bogen kann nah aussehen, während Details außerhalb der Silhouette falsch sind.
- **Die Schlussfolgerungen gelten nur für das Beispiel.** 13 Teile, zehn Einstellungen, dieses Timing und diese Abweichungen gehören zur Ventilator-Fallstudie und sind keine Vorgaben für andere Objekte.
- **Audio liegt nicht in git.** Der Film referenziert `examples/fan/video/assets/audio/mix.wav`, das als Release-Asset verteilt wird. Ohne die Datei ist das Projekt unvollständig, sie muss also vor `check` oder `render` zurückgelegt werden.
- **Version fixiert.** Die Befehle pinnen `hyperframes@0.9.36`, die Version, mit der das Beispiel gebaut wurde. Andere Versionen können sich anders verhalten; eine Kompatibilitätsliste wird hier nicht behauptet.
- **Drei der vier Beispielwerkzeuge laufen nicht unverändert.** Es sind historische Messskripte, die auf den ursprünglichen Arbeitsbereich des Autors zeigen. Parametrisierte Fassungen liegen in `scripts/`.
- **Der GIF-Schritt ist manuell.** gif-master läuft im Browser, der Download verlangt Anmeldung, und es gibt 3 kostenlose Downloads pro Tag. Das Repository automatisiert diesen Schritt nicht.
- **Rendern braucht einen echten Browser und ffmpeg.** HyperFrames erfasst Frames über Chrome, also kann ein Rechner ohne nutzbaren Browser den Film nicht rendern.

## Lizenz

- **Code** – MIT. Volltext in [`LICENSE`](LICENSE).
- **Fotos und gerenderte Medien** – die sechs Referenzfotos unter `examples/fan/reference/`, die Standbilder unter `examples/fan/out/` und der Film `fan-teardown-43s.mp4` stehen unter [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Namensnennung: **Mng12345/model-by-coding**, mit Link auf https://github.com/Mng12345/model-by-coding.
- **Drittbibliotheken und -materialien** behalten ihre eigenen Lizenzen; die eingecheckten three.js, GSAP, HyperFrames sowie die Schriften Inter/Inter Tight sind in [`README-LICENSES.md`](README-LICENSES.md) aufgeführt.

Fällt eine Nutzung unter keine dieser Lizenzen, vor der Wiederverwendung bitte ein Issue im Repository öffnen.

## Danksagung und Links

- [three.js](https://threejs.org) – MIT. Geometrie, Materialien und Renderer des Modells sind three.js.
- [GSAP](https://gsap.com) 3.13.0 – genutzt unter der [GSAP-Standardlizenz](https://gsap.com/standard-license). Die eingecheckte Kopie behält ihren Lizenzkopf.
- [HyperFrames](https://github.com/heygen-com/hyperframes) 0.9.36 – das HTML-zu-Video-Werkzeug, mit dem der Film gerendert wurde. Projektseite: https://hyperframes.heygen.com
- [gif-master.com](https://gif-master.com) – das browserbasierte Video-zu-GIF-Werkzeug aus Schritt 4.
- Inter und Inter Tight – Webfonts unter der SIL Open Font License 1.1; die Lizenztexte liegen neben den Schriftdateien in `examples/fan/video/assets/fonts/`.
- Die Referenzfotos hat der Autor aufgenommen; Marken- und Typenschilder wurden vor der Veröffentlichung unscharf gemacht. Das Modell trägt kein Branding. Das ist eine Geometriestudie, keine vom Hersteller gebilligte Nachbildung.
- Repository: https://github.com/Mng12345/model-by-coding
- Film auf YouTube: https://youtu.be/cwNxK5GSSjY
- Releases: https://github.com/Mng12345/model-by-coding/releases/latest
- Issues: https://github.com/Mng12345/model-by-coding/issues

Das Ventilator-Beispiel ist ein Objekt und ein Film. Wiederverwendbar sind die Messnotizen, die Prüfung aus derselben Kamera und die Methode, das Modell als Code zu serialisieren – nicht die konkreten Zahlen des Ventilators.
