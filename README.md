# DustSensor Visualization

Dit project automatiseert het uitlezen van een lokale fijnstof- en klimaatsensor (gebaseerd op de Luftdaten/Sensor.community firmware) via een Python-script. De data wordt opgeslagen in een SQLite3-database, waarna er automatisch elke 5 minuten een transparante trendgrafiek wordt gegenereerd die rechtstreeks via Conky op het bureaublad wordt getoond.

## 🚀 Functionaliteiten
* **Data-extractie:** Leest live `PM2.5`, `PM10`, temperatuur en luchtvochtigheid uit van de sensor-HTML.
* **Historische Opslag:** Bewaart alle metingen efficiënt in een lokale SQLite3-database.
* **Datavisualisatie:** Genereert een transparante grafiek met een 4-uurs voortschrijdend gemiddelde (rolling mean) om trends vloeiend te tonen.
* **Geoptimaliseerd voor Conky:** Slaat de grafiek atomair op in shared memory (`/dev/shm`) om flikkeringen of I/O-vertraging op het bureaublad te voorkomen.

---

## 📊 Database Structuur

De metingen worden opgeslagen in een SQLite3-database (`metingen.db`) met de volgende tabelstructuur:

```sql
CREATE TABLE metingen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    pm25 REAL NOT NULL,
    pm10 REAL NOT NULL,
    temp REAL,
    hum REAL
);
```

---

## 🛠️ Installatie & Vereisten

### 1. Afhankelijkheden installeren
Zorg ervoor dat Python 3 en Git aanwezig zijn op je systeem, en installeer de benodigde bibliotheken:

```bash
sudo apt update
sudo apt install python3-pip conky-all
pip install pandas matplotlib beautifulsoup4 requests
```

### 2. Bestanden structureren
Plaats de scripts in de gewenste map (bijvoorbeeld `~/git/dustSensor`).

dustSensor/
├── plot_fijnstof_trend.py  # Het hoofdscript voor data-extractie en plotten
├── .conky_fijnstof.conf    # De Conky visualisatie-instellingen
├── .gitignore              # Voorkomt dat database/afbeeldingen op GitHub belanden
└── README.md               # Deze handleiding

---

## ⏱️ Automatisering (Cronjob)

Om de data elke 5 minuten live op te halen en de grafiek te verversen, voegen we een cronjob toe. 

1. Open de crontab-editor:
   ```bash
   crontab -e
   ```
2. Voeg de volgende regel onderaan toe (pas het pad aan naar jouw situatie):
   ```text
   */5 * * * * cd /home/jan/git/dustSensor && /usr/bin/python3 plot_fijnstof_trend.py >> /home/jan/git/dustSensor/cron.log 2>&1
   ```

De output en eventuele fouten worden gelogd in `cron.log`.

---

## 💻 Conky Visualisatie

De grafiek wordt linksonder op je bureaublad getoond via Conky. Omdat het script gebruikmaakt van shared memory (`/dev/shm`), presteert dit ultrasnel en zonder haperingen.

Start de Conky-monitor met het volgende commando:

```bash
conky -c ~/.conky_fijnstof.conf &
```

### Automatisch opstarten bij inloggen
Om Conky automatisch te starten wanneer je pc opstart, voeg je het bovenstaande commando toe aan je **Startup Applications** (Opstarttoepassingen) in je Linux-desktopomgeving.

---

## 📄 Licentie
Dit project is vrij te gebruiken en aan te passen voor eigen domotica- en hobbydoeleinden.
