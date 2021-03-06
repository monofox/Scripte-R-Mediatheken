# Scripte ÖR Mediatheken (und ein paar mehr)

Dieses Archiv bietet Scripte zum Extrahieren von Videos aus den ÖR Mediatheken.

## Dependencies
Voraussetzungen sind die in `requirements.txt` beschriebenen Python-Module, Python 3 und ein Linux-System.

Aktuell sind die Videoplayer derzeit hartkodiert in den Scripten abgelegt.

## Aufrufe

In allen Fällen sollte die Scripte in der PATH-Umgebungsvariablen verfügbar sein.

### ARD

Zum Abruf eines Videos aus der ARD-Mediathek (der neuen) einfach die URL aus dem Browser kopieren und einsetzen:
```sh
  $ ./ardPlay https://www.ardmediathek.de/daserste/player/Y3JpZDovL2Rhc2Vyc3RlLmRlL3RzMTAwcy82YWJmMDFjNy1kZWY1LTRhYjMtODNkOS0xN2FkNDJlMWUyMTAvMQ/tagesschau-in-100-sekunden
```

### ZDF

Zum Abruf eines Videos aus der ZDF-Mediathek einfach die URL aus dem Browser kopieren und einsetzen:
```sh
  $ ./zdfStream --play https://www.zdf.de/comedy/urban-priol-tilt-tschuessikowski-2018/tilt-tschuessikowski2018-100.html
```

### 3sat

Zum Abruf eines Videos aus der 3sat-Mediathek einfach die URL aus dem Browser kopieren und einsetzen:
```sh
  $ ./3satStream --play 'http://www.3sat.de/mediathek/?mode=play&obj=78027'
```

Wichtig ist hier, dass die URL die Objektnummer derzeit noch enthalten muss (wohingegen URLs wie http://www.3sat.de/webtv/?180311_lisa_eckhart_kabarett.rm oder http://www.3sat.de/page/?source=/kleinkunst/196667/index.html derzeit nicht funktionieren).

### ARTE

Zum Abruf eines Videos aus der ARTE-Mediathek einfach die URL aus dem Browser kopieren und einsetzen:
```sh
  $ ./artePlay https://www.arte.tv/de/videos/083947-000-A/carl-orff-carmina-burana/
```

Im Falle von ARTE werden die entsprechenden unterschiedlichen Sprachen und Qualität aufgeschlüsselt.

### KiKA

Zum Abruf eines Videos aus der KiKA-Mediathek einfach die URL aus dem Browser kopieren und einsetzen:
```sh
  $ ./kikaStream --play https://www.kika.de/videos/sendung121052_zc-dbf2caa8_zs-5d23b3af.html
```

### Berliner Philharmoniker (Digital Concert Hall)

Zum Abruf eines Videos aus der Digital Concert Hall der Berliner Philharmoniker einfach die URL aus dem Browser kopieren und einsetzen.
Derzeit sucht das Script den besten Stream (mit der höchsten Auflösung, das könnte natürlich ggf. in der ein oder anderen Situation ärgerlich sein).

Aufruf via:
```sh
  $ ./berphilStream --play https://www.digitalconcerthall.com/de/concert/52502
```

Filme und Interviews werden ebenso unterstützt. Leider ist der Betreiber der Plattform nicht daran interessiert, die APIs für jedermann zu öffnen. Ohne entsprechenden Client Secret (OAuth) ist ein Zugriff nicht möglich. Gerne den Betreiber anschreiben und anfragen.

## Livestreams

Die Livestreams lassen sich mit Aufruf des jeweiligen Senderscripts öffnen. Die hinterlegten URLs sind (derzeit) die höchst verfügbaren Auflösungen.

## Contributions
Contributions, Proposals, Feedback sind herzlich willkommen.

## Lizenz
GNU GPL V3+
