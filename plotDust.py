import os

import sqlite3
import matplotlib.pyplot as plt
import pandas as pd

# Instellingen voor de database en uitvoer
DB_NAME = "/home/jan/db/sensor.db"  # Pas dit aan naar de exacte naam van jouw databasebestand

# Paden in shared memory (/dev/shm)
FINAL_OUTPUT = "/dev/shm/dust.png"
TEMP_OUTPUT = "/dev/shm/dust.tmp.png"

def genereer_grafiek():
    # 1. Maak verbinding met de SQLite-database
    try:
        conn = sqlite3.connect(DB_NAME)
    except sqlite3.Error as e:
        print(f"Fout bij openen van database: {e}")
        return

    # 2. Lees de data in een Pandas DataFrame
    # We selecteren de benodigde kolommen uit de tabel 'metingen'
    query = "SELECT timestamp, pm25, pm10 FROM metingen ORDER BY timestamp"
    df = pd.read_sql_query(query, conn)

    # Sluit de databaseverbinding netjes
    conn.close()

    if df.empty:
        print("Geen data gevonden in de tabel 'metingen'.")
        return

    # 3. Data voorbereiden: zet de timestamp om naar een echt datum/tijd-type
    df["timestamp"] = pd.to_datetime(df["timestamp"])


    # Zet de timestamp tijdelijk als index, dit is nodig voor een rolling window op basis van tijd ('4h')
    df.set_index("timestamp", inplace=True)


    # 4. Bereken het voortschrijdend gemiddelde van de laatste 4 uur
    # '4h' kijkt naar het daadwerkelijke tijdsverschil, min_periods=1 zorgt dat er direct een lijn start
    df["pm25_smooth"] = df["pm25"].rolling("4h", min_periods=1).mean()
    df["pm10_smooth"] = df["pm10"].rolling("4h", min_periods=1).mean()

    # Breng de timestamp weer terug als gewone kolom voor het plotten
    df.reset_index(inplace=True)


    # 5. De grafiek opbouwen
    # plt.figure(figsize=(10, 6))  # Breedte en hoogte van de grafiek
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_facecolor("none")
    fig.patch.set_facecolor("none")


    # Teken de originele (ruwe) meetpunten met een dunne, transparante lijn
    ax.plot(
        df["timestamp"],
        df["pm25"],
        color="#2ca02c",
        alpha=0.5,
        linestyle="--",
        label="PM2.5 (ruwe data)",
    )
    ax.plot(
        df["timestamp"],
        df["pm10"],
        color="#1f77b4",
        alpha=0.5,
        linestyle="--",
        label="PM10 (ruwe data)",
    )

    # Teken de dikke, vloeiende trendlijnen (4-uurs gemiddelde)
    ax.plot(
        df["timestamp"],
        df["pm25_smooth"],
        color="#2ca02c",
        linewidth=2.5,
        label="PM2.5 (4u gemiddelde)",
    )
    ax.plot(
        df["timestamp"],
        df["pm10_smooth"],
        color="#1f77b4",
        linewidth=2.5,
        label="PM10 (4u gemiddelde)",
    )


    # 5. Grafiek opmaken en stylen
    # plt.title("Fijnstofmetingen (PM2.5 vs PM10)", fontsize=14, fontweight="bold")
    # plt.xlabel("Tijdstip", fontsize=11)
    # plt.ylabel("Concentratie (µg/m³)", fontsize=11)

    # ax.set_xlabel("Tijdstip", fontsize=14, color="white")
    ax.set_ylabel("Concentratie (µg/m³)", fontsize=14, color="white")

    # Instellingen voor de as-waarden (getallen zelf)
    ax.tick_params(colors="white", labelsize=12)
    for spine in ax.spines.values():
        spine.set_color("white")

    # Zorg dat de datums op de X-as mooi schuin staan en leesbaar zijn
    # plt.gcf().autofmt_xdate()
    # fig.autofmt_xdate()
    # Maak de datums op de X-as schuin (30 graden) en geef ze de ruimte
    plt.xticks(rotation=30, ha="right")

    # Voeg een raster toe op de achtergrond voor betere leesbaarheid
    # plt.grid(True, linestyle="--", alpha=0.6)
    ax.grid(True, linestyle="--", alpha=0.3, color="white")

    # Voeg de legende toe
    # plt.legend(loc="upper left", fontsize=10)
    leg = ax.legend(loc="upper left", fontsize=12, facecolor="none", edgecolor="none")
    for text in leg.get_texts():
        text.set_color("white")

    # Zorg dat alle elementen netjes binnen het figuur passen
    plt.tight_layout()

    # 6. De grafiek tonen en optioneel opslaan
    # plt.savefig(IMAGE_OUTPUT, dpi=150)  # Slaat de grafiek op als PNG
    # print(f"Grafiek succesvol opgeslagen als '{IMAGE_OUTPUT}'")
    # plt.show()  # Opent een pop-up venster met de interactieve grafiek


    # 7. Sla eerst op als tijdelijk bestand en vervang daarna atomair
    try:
        # Schrijf naar de .tmp.png file in shared memory
        plt.savefig(TEMP_OUTPUT, dpi=120, transparent=True)
        plt.close()

        # Atomaire verplaatsing/herbenoeming binnen /dev/shm
        os.replace(TEMP_OUTPUT, FINAL_OUTPUT)
        print(f"Grafiek succesvol atomair bijgewerkt in {FINAL_OUTPUT}")
    except Exception as e:
        print(f"Fout bij wegschrijven van grafiek: {e}")



if __name__ == "__main__":
    genereer_grafiek()

