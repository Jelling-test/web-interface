import db
import json
from datetime import datetime

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

def safe_format(value, default=''):
    return str(value) if value is not None else default

if __name__ == "__main__":
    # Hent alle målere med den nye funktion
    meters = db.get_all_meters()
    
    # Vis resultatet i pænt formateret JSON
    print(json.dumps(meters, indent=2, cls=CustomEncoder))
    
    # Vis statistik
    print(f"\n{'='*80}")
    print(f"MÅLER STATUS RAPPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"{'MAC':10} | {'STATUS':10} | {'STRØM':10} | {'FEJL':15} | {'NAVN'}")
    print(f"{'-'*10}-+-{'-'*10}-+-{'-'*10}-+-{'-'*15}-+-{'-'*30}")
    
    for meter in meters:
        print(f"{safe_format(meter.get('mac')):10} | {safe_format(meter.get('status'), 'ukendt'):10} | {safe_format(meter.get('power'), 'ukendt'):10} | {safe_format(meter.get('error'), 'Ingen fejl'):15} | {safe_format(meter.get('name'))}")
    
    print(f"{'='*80}")
    print(f"Fandt {len(meters)} målere i alt")
    
    # Vis fejlstatistik
    error_count = sum(1 for m in meters if m.get('error'))
    print(f"Målere med fejl: {error_count}")
    print(f"{'='*80}")
