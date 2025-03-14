import db
import json
from datetime import datetime
from sqlalchemy.sql import text

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

if __name__ == "__main__":
    # Hent specifik måler
    mac = '0884E237'
    try:
        print(f"\n{'='*80}")
        print(f"Henter information om måler {mac}")
        
        # Tjek om måleren findes i maalerinfo tabellen
        with db.engine.connect() as connection:
            info_query = text("SELECT * FROM maalerinfo WHERE mac = :mac")
            info_result = connection.execute(info_query, {"mac": mac})
            meter_info = dict(info_result.fetchone() or {})
            
            if meter_info:
                print(f"\nMålerinfo fundet:")
                print(json.dumps(meter_info, indent=2, cls=CustomEncoder))
            else:
                print(f"\nIngen målerinfo fundet for {mac}")
            
        # Tjek energimaaling tabellen
        print(f"\n{'='*80}")
        print(f"Tjekker energimaalinger for {mac}")
        
        with db.engine.connect() as connection:
            reading_query = text("SELECT * FROM energimaaling WHERE mac = :mac ORDER BY tidspunkt DESC LIMIT 1")
            reading_result = connection.execute(reading_query, {"mac": mac})
            reading = dict(reading_result.fetchone() or {})
            
            if reading:
                print(f"\nSeneste måling fundet:")
                print(json.dumps(reading, indent=2, cls=CustomEncoder))
            else:
                print(f"\nIngen målinger fundet for {mac}")
            
        # Tjek maalerstatus tabellen
        print(f"\n{'='*80}")
        print(f"Tjekker status for {mac}")
        
        try:
            with db.engine.connect() as connection:
                status_query = text("SELECT * FROM maalerstatus WHERE mac = :mac ORDER BY tidspunkt DESC LIMIT 1")
                status_result = connection.execute(status_query, {"mac": mac})
                row = status_result.fetchone()
                
                if row:
                    status = {col: val for col, val in zip(status_result.keys(), row)}
                    print(f"\nSeneste status fundet:")
                    print(json.dumps(status, indent=2, cls=CustomEncoder))
                else:
                    print(f"\nIngen status fundet for {mac}")
        except Exception as e:
            print(f"\nFejl under forespørgsel af status: {e}")
            
    except Exception as e:
        print(f"\nFejl under forespørgsel: {e}")
    
    print(f"\n{'='*80}")
