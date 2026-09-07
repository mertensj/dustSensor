import os
import sys
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# Paden in shared memory (/dev/shm)
FINAL_OUTPUT = "/dev/shm/temp.png"
TEMP_OUTPUT = "/dev/shm/temp.tmp.png"



# 1. Parameter voor het aantal dagen uitlezen
# Standaard is 3 dagen, tenzij er een argument wordt meegegeven (bijv. python3 plot.py 5)
aantal_dagen = 3
if len(sys.argv) > 1:
    try:
        aantal_dagen = int(sys.argv[1])
        if aantal_dagen <= 0:
            raise ValueError
    except ValueError:
        print("Fout: Geef een geldig positief getal op voor het aantal dagen. Systeem valt terug op 3 dagen.")
        aantal_dagen = 3

# 2. Verbinding maken met de database
DB_FILE = "/home/jan/db/sensor.db"

if not os.path.exists(DB_FILE):
    if os.path.exists("sensor.db"):
        DB_FILE = "sensor.db"
    else:
        print("Fout: Kan sensor.db niet vinden.")
        exit(1)

conn = sqlite3.connect(DB_FILE)

# 3. Data ophalen op basis van de parameter (X dagen)
query = f"""
SELECT timestamp, temp 
FROM metingen 
WHERE timestamp >= DATETIME('now', '-{aantal_dagen} days')
  AND temp IS NOT NULL
  AND temp != 'N/A'
ORDER BY timestamp ASC;
"""

df = pd.read_sql_query(query, conn)
conn.close()

if df.empty:
    print(f"Geen geldige data gevonden voor de afgelopen {aantal_dagen} dagen.")
    exit()

# Tijdreeksen correct instellen
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)
df.sort_index(inplace=True)
df['temp'] = pd.to_numeric(df['temp'], errors='coerce')
df.dropna(subset=['temp'], inplace=True)

# 4. Bereken de MIN en MAX per kalenderdag
dagelijkse_stats = df.groupby(df.index.date)['temp'].agg(['min', 'max'])

# 5. De grafiek genereren met een transparante achtergrond
fig, ax = plt.subplots(figsize=(12, 6), facecolor='none')
ax.set_facecolor('none')

# Alle actuele metingen plotten met een dunnere lijn en kleine gele bolletjes
ax.plot(df.index, df['temp'], color="orange", linewidth=0.8, alpha=0.4, zorder=2)
ax.scatter(df.index, df['temp'], color="gold", edgecolors="darkorange", s=8, linewidths=0.5, zorder=3)

# Gekleurde referentielijnen trekken die enkel gelden voor de specifieke dag
for dag, stats in dagelijkse_stats.iterrows():
    dag_data = df[df.index.date == dag]
    if not dag_data.empty:
        start_tijd = dag_data.index.min()
        eind_tijd = dag_data.index.max()
        
        # Horizontale MIN en MAX lijnen per dag
        ax.hlines(stats['max'], start_tijd, eind_tijd, colors="crimson", linestyles="--", linewidth=1.2, zorder=4)
        ax.hlines(stats['min'], start_tijd, eind_tijd, colors="royalblue", linestyles="--", linewidth=1.2, zorder=4)
        
        # Waarden als tekst toevoegen
        ax.text(start_tijd, stats['max'] + 0.15, f"{stats['max']:.1f}°C", color="crimson", fontsize=14, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.6))
        ax.text(start_tijd, stats['min'] - 0.45, f"{stats['min']:.1f}°C", color="royalblue", fontsize=14, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.6))

# X-as verdeling instellen (interval schaalt dynamisch mee als je veel dagen kiest)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %H:%M'))
interval_uren = 3 if aantal_dagen <= 3 else (6 if aantal_dagen <= 7 else 12)
ax.xaxis.set_major_locator(mdates.HourLocator(interval=interval_uren))
plt.xticks(rotation=45)


# === Y-AS TITEL TERUGZETTEN (IN HET WIT) ===
ax.set_ylabel("Temperatuur (°C)", color="white", fontsize=11, labelpad=10)


# === HIER WORDEN DE ASSEN EN TICK-LABELS WIT GEMAAKT ===
ax.tick_params(colors='white', which='both')  # Maakt de getallen en streepjes wit
for spine in ax.spines.values():
    spine.set_color('white')  # Maakt de buitenste kaderlijnen van de grafiek wit

# Assen styling
ax.grid(True, linestyle="--", alpha=0.4, color="white")
ax.set_ylim(df['temp'].min() - 1.2, df['temp'].max() + 1.2)

plt.tight_layout()

# 6. Opslaan op de RAM-disk met behoud van transparantie
#output_path = "/dev/shm/temp.png"
#plt.savefig(output_path, dpi=300, transparent=True)
#plt.close()

# 7. Sla eerst op als tijdelijk bestand en vervang daarna atomair
try:
     # Schrijf naar de .tmp.png file in shared memory
     plt.savefig(TEMP_OUTPUT, dpi=150, transparent=True)
     plt.close()

     # Atomaire verplaatsing/herbenoeming binnen /dev/shm
     os.replace(TEMP_OUTPUT, FINAL_OUTPUT)
     print(f"Grafiek van de afgelopen {aantal_dagen} dagen succesvol atomair bijgewerkt in {FINAL_OUTPUT}")
except Exception as e:
     print(f"Fout bij wegschrijven van grafiek: {e}")

