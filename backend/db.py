from sqlalchemy import create_engine, text
import pymysql
from config import DB_CONFIG
import datetime

# Opret database engine
def get_db_connection_string():
    return f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

engine = create_engine(get_db_connection_string())

def test_connection():
    """Test forbindelsen til databasen"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Fejl ved forbindelse til database: {e}")
        return False

def get_all_meters():
    """Hent alle målere fra systemet, inklusive dem uden målinger"""
    try:
        with engine.connect() as connection:
            # Hent alle MAC-adresser fra både energimaaling og maalerstatus
            query = text("""
                SELECT DISTINCT mac FROM (
                    SELECT mac FROM energimaaling
                    UNION
                    SELECT mac FROM maalerstatus
                ) AS all_meters
            """)
            result = connection.execute(query)
            all_macs = [row[0] for row in result]
            
            if not all_macs:
                print("Ingen målere fundet i systemet!")
                return []
            
            # Hent seneste måling for hver måler (hvis der er nogen)
            meters = []
            for mac in all_macs:
                meter = {"mac": mac, "status": "offline", "error": "Ingen data"}
                
                # Hent seneste måling
                try:
                    reading_query = text("""
                        SELECT 
                            mac, 
                            totalKwh, 
                            CURRENT_TIMESTAMP() as db_tidspunkt
                        FROM energimaaling 
                        WHERE mac = :mac
                        ORDER BY tidspunkt DESC 
                        LIMIT 1
                    """)
                    reading_result = connection.execute(reading_query, {"mac": mac})
                    reading = reading_result.fetchone()
                    
                    if reading:
                        meter.update({
                            "lastSeen": reading.db_tidspunkt.strftime('%Y-%m-%d %H:%M:%S') if reading.db_tidspunkt else None,
                            "lastReading": float(reading.totalKwh) if hasattr(reading, 'totalKwh') else 0.0,
                            "error": None
                        })
                except Exception as e:
                    meter['error'] = f"Fejl ved hentning af målinger: {str(e)}"
                
                # Hent seneste status
                try:
                    status_query = text("""
                        SELECT * FROM maalerstatus 
                        WHERE mac = :mac
                        ORDER BY tidspunkt DESC 
                        LIMIT 1
                    """)
                    status_result = connection.execute(status_query, {"mac": mac})
                    status = status_result.fetchone()
                    
                    if status:
                        meter.update({
                            "status": "online" if status.status == "Tændt" else "offline",
                            "power": "tændt" if status.status == "Tændt" else "slukket",
                            "sidste_status_tid": status.tidspunkt.strftime('%Y-%m-%d %H:%M:%S') if status.tidspunkt else None
                        })
                except Exception as e:
                    meter['error'] = f"Fejl ved hentning af status: {str(e)}"
                
                # Hent navngivning
                try:
                    name_query = text("SELECT name, nummer FROM maalerinfo WHERE mac = :mac")
                    name_result = connection.execute(name_query, {"mac": mac})
                    info_row = name_result.fetchone()
                    if info_row:
                        meter["name"] = info_row.name if info_row.name else "Unavngivet"
                        meter["number"] = info_row.nummer if info_row.nummer else None
                    else:
                        meter["name"] = "Unavngivet"
                        meter["number"] = None
                except Exception as e:
                    meter['error'] = f"Fejl ved hentning af navn: {str(e)}"
                
                meters.append(meter)
            
            return meters
    except Exception as e:
        print(f"Fejl ved hentning af målere: {e}")
        return []

def get_meter_info(mac):
    """Hent information om en specifik måler"""
    try:
        with engine.connect() as connection:
            # Opret et basisobjekt med MAC-adressen
            meter_data = {
                "mac": mac,
                "info": {},
                "last_reading": {},
                "status": {}
            }
            
            # Tjek om der er et navngivet navn for måleren
            name_query = text("SELECT * FROM maalerinfo WHERE mac = :mac")
            name_result = connection.execute(name_query, {"mac": mac})
            name_row = name_result.fetchone()
            
            if name_row:
                # Konverter row til dict på en sikker måde
                info_dict = {}
                for key in name_row._mapping.keys():
                    info_dict[key] = name_row._mapping[key]
                meter_data["info"] = info_dict
            
            # Hent seneste måling
            last_reading_query = text("""
                SELECT m1.* FROM energimaaling m1
                INNER JOIN (
                    SELECT mac, MAX(tidspunkt) as seneste_tidspunkt
                    FROM energimaaling
                    WHERE mac = :mac
                    GROUP BY mac
                ) m2 ON m1.mac = m2.mac AND m1.tidspunkt = m2.seneste_tidspunkt
            """)
            last_reading_result = connection.execute(last_reading_query, {"mac": mac})
            last_reading_row = last_reading_result.fetchone()
            
            if last_reading_row:
                # Konverter row til dict på en sikker måde
                reading_dict = {}
                for key in last_reading_row._mapping.keys():
                    reading_dict[key] = last_reading_row._mapping[key]
                meter_data["last_reading"] = reading_dict
            
            # Hent seneste status
            status_query = text("""
                SELECT s1.* FROM maalerstatus s1
                INNER JOIN (
                    SELECT mac, MAX(tidspunkt) as seneste_tidspunkt
                    FROM maalerstatus
                    WHERE mac = :mac
                    GROUP BY mac
                ) s2 ON s1.mac = s2.mac AND s1.tidspunkt = s2.seneste_tidspunkt
            """)
            status_result = connection.execute(status_query, {"mac": mac})
            status_row = status_result.fetchone()
            
            if status_row:
                # Konverter row til dict på en sikker måde
                status_dict = {}
                for key in status_row._mapping.keys():
                    status_dict[key] = status_row._mapping[key]
                meter_data["status"] = status_dict
            
            return meter_data
    except Exception as e:
        print(f"Fejl ved hentning af målerinfo: {e}")
        return {"error": str(e), "mac": mac}

def get_meter_readings(mac, limit=200):
    """Hent de seneste målinger for en specifik måler"""
    try:
        with engine.connect() as connection:
            # Debug: Udskriv MAC-adressen
            print(f"Henter målinger for MAC: '{mac}', type: {type(mac)}")
            
            # Tjek først om der er data for denne MAC-adresse
            count_query = text("SELECT COUNT(*) FROM energimaaling WHERE mac = :mac")
            count_result = connection.execute(count_query, {"mac": mac}).fetchone()
            print(f"Antal målinger fundet: {count_result[0]}")
            
            # Hent målinger
            query = text("""
                SELECT * FROM energimaaling 
                WHERE mac = :mac 
                ORDER BY tidspunkt DESC 
                LIMIT :limit
            """)
            result = connection.execute(query, {"mac": mac, "limit": limit})
            
            # Korrekt konvertering af rækker til dictionaries
            readings = []
            for row in result:
                row_dict = {}
                for column, value in zip(row._mapping.keys(), row):
                    # Konverter dato-objekter til strenge
                    if isinstance(value, (datetime.date, datetime.datetime)):
                        row_dict[column] = value.isoformat()
                    else:
                        row_dict[column] = value
                readings.append(row_dict)
            
            print(f"Returnerer {len(readings)} målinger")
            return readings
    except Exception as e:
        print(f"Fejl ved hentning af måleraflæsninger: {e}")
        return []

def get_daily_readings(mac, days=30):
    """Hent de seneste daglige målinger for en specifik måler"""
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT * FROM energimaaling_daglig 
                WHERE mac = :mac 
                ORDER BY dato DESC 
                LIMIT :days
            """)
            result = connection.execute(query, {"mac": mac, "days": days})
            
            # Korrekt konvertering af rækker til dictionaries
            readings = []
            for row in result:
                row_dict = {}
                for column, value in zip(row._mapping.keys(), row):
                    # Konverter dato-objekter til strenge
                    if isinstance(value, (datetime.date, datetime.datetime)):
                        row_dict[column] = value.isoformat()
                    else:
                        row_dict[column] = value
                readings.append(row_dict)
                
            return readings
    except Exception as e:
        print(f"Fejl ved hentning af daglige aflæsninger: {e}")
        return []

def get_unnamed_meters():
    """Find målere der har målinger men ikke er navngivet endnu med detaljerede oplysninger"""
    try:
        meters = []
        with engine.connect() as connection:
            # Først find tidspunktet for den seneste måling i databasen
            latest_query = text("SELECT MAX(tidspunkt) as nyeste_tidspunkt FROM energimaaling")
            latest_result = connection.execute(latest_query).fetchone()
            seneste_tidspunkt = latest_result[0]
            
            if not seneste_tidspunkt:
                print("Ingen målinger fundet i databasen!")
                return []
                
            print(f"Seneste måling i databasen: {seneste_tidspunkt}")
            
            # Hent målere der findes i energimaaling men ikke i maalerinfo
            # eller har NULL/tom værdi i name-feltet i maalerinfo
            # Bestem online/offline status baseret på seneste måling (30 min interval)
            query = text("""
                SELECT 
                    e.mac, 
                    MAX(e.tidspunkt) as sidst_set,
                    CASE WHEN MAX(e.tidspunkt) >= DATE_SUB(:seneste_tid, INTERVAL 30 MINUTE) 
                         THEN 'online' ELSE 'offline' END as status,
                    (SELECT totalKwh FROM energimaaling 
                     WHERE mac = e.mac 
                     ORDER BY tidspunkt DESC LIMIT 1) as seneste_totalKwh,
                    COUNT(DISTINCT DATE(e.tidspunkt)) as antal_dage_med_data
                FROM energimaaling e
                LEFT JOIN maalerinfo m ON e.mac = m.mac
                WHERE m.mac IS NULL OR m.name IS NULL OR m.name = '' OR m.name = 'Unavngivet'
                GROUP BY e.mac
                ORDER BY sidst_set DESC
            """)
            result = connection.execute(query, {"seneste_tid": seneste_tidspunkt})
            for row in result:
                # Konverter SQLAlchemy Row til dict manuelt
                # Konverter Decimal værdier til float
                seneste_kwh = row[3]
                if seneste_kwh is not None:
                    # Sikrer konvertering fra Decimal til float
                    seneste_kwh = float(seneste_kwh)
                
                meter = {
                    "mac": row[0],
                    "sidst_set": row[1],
                    "status": row[2],
                    "seneste_totalKwh": seneste_kwh,
                    "antal_dage_med_data": row[4],
                    "name": None,
                    "number": None
                }
                meters.append(meter)
            
            # Hent også målere fra maalerinfo som er unavngivne men ikke har målinger
            query2 = text("""
                SELECT 
                    m.mac,
                    NULL as sidst_set,
                    'offline' as status,
                    NULL as seneste_totalKwh,
                    0 as antal_dage_med_data
                FROM maalerinfo m
                LEFT JOIN energimaaling e ON m.mac = e.mac
                WHERE e.mac IS NULL AND (m.name IS NULL OR m.name = '' OR m.name = 'Unavngivet')
            """)
            result2 = connection.execute(query2)
            for row in result2:
                # Tjek om denne måler allerede er tilføjet (undgå dubletter)
                if not any(m['mac'] == row[0] for m in meters):
                    meter = {
                        "mac": row[0],
                        "sidst_set": None,
                        "status": "offline",
                        "seneste_totalKwh": None,
                        "antal_dage_med_data": 0,
                        "name": None,
                        "number": None
                    }
                    meters.append(meter)
            
            # Hent alle målere markeret som "Unavngivet" i maalerinfo tabellen
            query3 = text("""
                SELECT 
                    mac
                FROM maalerinfo
                WHERE name = 'Unavngivet'
            """)
            result3 = connection.execute(query3)
            for row in result3:
                # Tjek om denne måler allerede er tilføjet (undgå dubletter)
                if not any(m['mac'] == row[0] for m in meters):
                    meter = {
                        "mac": row[0],
                        "sidst_set": None,
                        "status": "offline",
                        "seneste_totalKwh": None,
                        "antal_dage_med_data": 0,
                        "name": None,
                        "number": None
                    }
                    meters.append(meter)
            
            # Log antal fundne målere til debugging
            print(f"Fandt {len(meters)} unavngivne målere: {[m['mac'] for m in meters]}")
            
            return meters
    except Exception as e:
        print(f"Fejl ved hentning af ubenævnte målere: {e}")
        return []

def update_meter_name(mac, name, number):
    """Opdater eller opret målerinfo med navn og nummer"""
    try:
        with engine.connect() as connection:
            # Tjek om MAC adressen allerede findes
            check_query = text("SELECT mac FROM maalerinfo WHERE mac = :mac")
            result = connection.execute(check_query, {"mac": mac})
            exists = result.fetchone() is not None
            
            if exists:
                # Opdater eksisterende måler
                update_query = text("""
                    UPDATE maalerinfo 
                    SET name = :name, nummer = :number
                    WHERE mac = :mac
                """)
                connection.execute(update_query, {"mac": mac, "name": name, "number": number})
            else:
                # Opret ny målerinfo
                insert_query = text("""
                    INSERT INTO maalerinfo (mac, name, nummer)
                    VALUES (:mac, :name, :number)
                """)
                connection.execute(insert_query, {"mac": mac, "name": name, "number": number})
            
            return True
    except Exception as e:
        print(f"Fejl ved opdatering af målernavn: {e}")
        return False

def delete_meter(mac):
    """Slet en måler og alle dens data"""
    try:
        with engine.connect() as connection:
            # Start en transaktion
            trans = connection.begin()
            try:
                # Slet fra maalerinfo
                connection.execute(text("DELETE FROM maalerinfo WHERE mac = :mac"), {"mac": mac})
                
                # Slet fra energimaaling
                connection.execute(text("DELETE FROM energimaaling WHERE mac = :mac"), {"mac": mac})
                
                # Slet fra energimaaling_daglig
                connection.execute(text("DELETE FROM energimaaling_daglig WHERE mac = :mac"), {"mac": mac})
                
                # Slet fra maalerstatus
                connection.execute(text("DELETE FROM maalerstatus WHERE mac = :mac"), {"mac": mac})
                
                # Commit transaktionen
                trans.commit()
                return True
            except Exception as e:
                # Hvis der opstår en fejl, rollback transaktionen
                trans.rollback()
                raise e
    except Exception as e:
        print(f"Fejl ved sletning af måler: {e}")
        return False

def check_meter_number_exists(number):
    """Tjek om et specifikt målernummer allerede er i brug"""
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT mac, name, nummer
                FROM maalerinfo
                WHERE nummer = :number
            """)
            result = connection.execute(query, {"number": number})
            row = result.fetchone()
            if row:
                return dict(row)
            return None
    except Exception as e:
        print(f"Fejl ved kontrol af målernummer: {e}")
        return None

def update_meter_info(mac, name, number):
    """Opdater eller opret en måler med navn og nummer i maalerinfo tabellen"""
    try:
        with engine.connect() as connection:
            # Tjek først om MAC adressen allerede eksisterer
            check_query = text("""
                SELECT mac FROM maalerinfo
                WHERE mac = :mac
            """)
            result = connection.execute(check_query, {"mac": mac})
            exists = result.fetchone() is not None
            
            if exists:
                # Opdater eksisterende måler
                update_query = text("""
                    UPDATE maalerinfo
                    SET name = :name, nummer = :number
                    WHERE mac = :mac
                """)
                connection.execute(update_query, {
                    "mac": mac,
                    "name": name,
                    "number": number
                })
            else:
                # Indsæt ny måler
                insert_query = text("""
                    INSERT INTO maalerinfo (mac, name, nummer)
                    VALUES (:mac, :name, :number)
                """)
                connection.execute(insert_query, {
                    "mac": mac,
                    "name": name,
                    "number": number
                })
            
            connection.commit()
            return True
    except Exception as e:
        print(f"Fejl ved opdatering af målerinfo: {e}")
        return False
