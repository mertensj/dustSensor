import os
import sqlite3
import requests

from datetime import datetime

# Instellingen
DB_FILE = "/home/jan/db/sensor.db"


def init_db():
    """Maakt de database en tabel aan met kolommen voor PM, temperatuur en vochtigheid."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Tabel aanmaken (inclusief temperatuur en luchtvochtigheid)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS metingen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            pm25 REAL NOT NULL,
            pm10 REAL NOT NULL,
            temp REAL,
            hum REAL
        )
        """
    )
    conn.commit()
    conn.close()



def log_to_db(pm10, pm25, temperature, humidity):
    """Slaat alle meetwaarden op in de SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Gegevens invoegen in de 5 kolommen (timestamp + 4 meetwaarden)
        cursor.execute(
            """
            INSERT INTO metingen (timestamp, pm25, pm10, temp, hum) 
            VALUES (?, ?, ?, ?, ?)
        """,
            (current_time, pm25, pm10, temperature, humidity),
        )

        conn.commit()
        #print( f"[{current_time}] Opgeslagen -> PM2.5: {pm25} | PM10: {pm10} | Temp: {temperature}°C | Hum: {humidity}%")

    except sqlite3.Error as e:
        print(f"Database fout: {e}")
    finally:
        conn.close()






def write_to_shm(filename, value):
    # Schrijft de waarde direct naar het Shared Memory (RAM)
    try:
        shm_path = f"/dev/shm/{filename}"
        with open(shm_path, "w") as f:
            f.write(str(value))
    except Exception as e:
        print(f"Fout bij schrijven naar {filename}: {e}")

def get_and_store_sensor_data(main_sensor_id):
    url_dust = f"https://data.sensor.community/airrohr/v1/sensor/{main_sensor_id}/"    

    # Standaardwaarden als de API offline is
    pm10, pm25, temp, hum = "N/A", "N/A", "N/A", "N/A"

    # 1. Fijnstof ophalen
    try:
        response = requests.get(url_dust, timeout=10)
        if response.status_code == 200 and response.json():
            # De API geeft een lijst van metingen; neem de nieuwste (index 0)
            latest = response.json()[0]
            for item in latest.get("sensordatavalues", []):
                if item["value_type"] == "P1":
                    pm10 = item["value"]
                elif item["value_type"] == "P2":
                    pm25 = item["value"]
    except Exception as e:
        print(f"Fout bij fijnstof: {e}")

    # 2. Temperatuur en Luchtvochtigheid ophalen (ID - 1)
    s_id = main_sensor_id - 1
    url = f"https://data.sensor.community/airrohr/v1/sensor/{s_id}/"    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.json():
             latest = response.json()[0]
             for item in latest.get("sensordatavalues", []):
                 if item["value_type"] == "temperature":
                     temp = item["value"]
                 elif item["value_type"] == "humidity":
                     hum = item["value"]
    except Exception as e:
        print(f"Fout bij temp en hum: {e}")

    # 3. Bewaren in Shared Memory (/dev/shm/)
    write_to_shm("pm10", pm10)
    write_to_shm("pm25", pm25)
    write_to_shm("temp", temp)
    write_to_shm("hum", hum)


    # 4. Bewaren in sqlite3
    log_to_db(pm10,pm25,temp,hum)


if __name__ == "__main__":
    # Initialiseer sqlite3
    init_db()
    # Jouw Sensor ID
    get_and_store_sensor_data(92620)

