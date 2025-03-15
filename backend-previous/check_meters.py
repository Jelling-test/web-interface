import pymysql
import pymysql.cursors
from datetime import datetime, timedelta
import sys
from config import DB_CONFIG

def connect_to_db():
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Fejl ved forbindelse til database: {e}")
        sys.exit(1)

def get_all_meters():
    """Hent alle målere med deres status (online/offline)"""
    connection = connect_to_db()
    
    try:
        with connection.cursor() as cursor:
            # Først find tidspunktet for den seneste måling i databasen
            cursor.execute("SELECT MAX(tidspunkt) as nyeste_tidspunkt FROM energimaaling")
            result = cursor.fetchone()
            seneste_tidspunkt = result['nyeste_tidspunkt']
            
            if not seneste_tidspunkt:
                print("Ingen målinger fundet i databasen!")
                return []
            
            # Beregn en grænse på 30 minutter fra seneste måling
            # Hvis en måler har sendt data inden for 30 minutter fra den 
            # seneste måling, betragtes den som online
            print(f"Seneste måling i databasen: {seneste_tidspunkt}")
            
            query = """
            SELECT 
                e.mac,
                MAX(e.tidspunkt) as sidst_set,
                (CASE WHEN MAX(e.tidspunkt) >= DATE_SUB(%s, INTERVAL 30 MINUTE) 
                      THEN 'online' ELSE 'offline' END) as status
            FROM energimaaling e
            GROUP BY e.mac
            ORDER BY sidst_set DESC
            """
            
            cursor.execute(query, (seneste_tidspunkt,))
            meters = cursor.fetchall()
            
            # Hent navngivne målere
            query_names = """
            SELECT mac, name FROM maalerinfo
            """
            cursor.execute(query_names)
            meter_names = {row['mac']: row['name'] for row in cursor.fetchall()}
            
            # Berig data med navngivningsstatus og navn
            for meter in meters:
                meter['name'] = meter_names.get(meter['mac'], 'Unavngivet')
                meter['named'] = meter['mac'] in meter_names
                
                # Beregn hvor lang tid siden sidste måling ift. seneste måling i databasen
                if meter['sidst_set']:
                    diff = seneste_tidspunkt - meter['sidst_set']
                    minutes_diff = diff.total_seconds() / 60
                    
                    if minutes_diff < 1:
                        meter['last_seen'] = "Nyeste måling"
                    elif minutes_diff < 60:
                        meter['last_seen'] = f"{int(minutes_diff)} minutter efter nyeste"
                    else:
                        meter['last_seen'] = f"{int(minutes_diff/60)} timer efter nyeste"
                else:
                    meter['last_seen'] = 'ukendt'
            
            return meters
    finally:
        connection.close()

if __name__ == "__main__":
    meters = get_all_meters()
    
    if not meters:
        print("Ingen målere fundet!")
        sys.exit(0)
    
    print(f"{'*'*80}")
    print(f"MÅLER STATUS RAPPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'*'*80}")
    print(f"{'MAC':10} | {'STATUS':10} | {'SIDST SET':25} | {'NAVN'}")
    print(f"{'-'*10}-+-{'-'*10}-+-{'-'*25}-+-{'-'*30}")
    
    for meter in meters:
        print(f"{meter['mac']:10} | {meter['status']:10} | {meter['last_seen']:25} | {meter['name']}")
    
    print(f"{'*'*80}")
    print(f"Fandt {len(meters)} målere i alt")
    
    # Vis statistik
    online_count = sum(1 for m in meters if m['status'] == 'online')
    offline_count = sum(1 for m in meters if m['status'] == 'offline')
    
    print(f"Online: {online_count} ({online_count/len(meters)*100:.1f}%)")
    print(f"Offline: {offline_count} ({offline_count/len(meters)*100:.1f}%)")
    print(f"{'*'*80}")
