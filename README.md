# Måler Overvågningssystem - Dokumentation

Dette dokument beskriver, hvordan du kan genopbygge og køre måler overvågningssystemet på en ny PC. Systemet består af en backend (Flask) og en frontend (Vue.js), der kommunikerer via API'er og Socket.IO, samt bruger MQTT til at kommunikere med målerne.

## Indholdsfortegnelse

1. [Systemkrav](#systemkrav)
2. [Mappestruktur](#mappestruktur)
3. [Installation](#installation)
   - [Docker Installation](#docker-installation)
   - [Opsætning af miljøvariabler](#opsætning-af-miljøvariabler)
   - [Bygning og opstart af containere](#bygning-og-opstart-af-containere)
4. [Systemarkitektur](#systemarkitektur)
   - [Backend](#backend)
   - [Frontend](#frontend)
   - [MQTT Integration](#mqtt-integration)
5. [Funktionalitet](#funktionalitet)
   - [Måler oversigt](#måler-oversigt)
   - [Måler detaljer](#måler-detaljer)
   - [Scanning efter nye målere](#scanning-efter-nye-målere)
6. [Fejlfinding](#fejlfinding)
7. [Vedligeholdelse](#vedligeholdelse)

## Systemkrav

For at køre systemet skal du have følgende installeret:

- Docker Desktop (nyeste version)
- Git (valgfrit, men anbefalet for versionsstyring)
- En moderne webbrowser (Chrome, Firefox, Edge)

## Mappestruktur

Systemet er organiseret i følgende mappestruktur:

```
måler system/
├── backend/                # Python Flask backend
│   ├── app.py              # Hovedapplikation
│   ├── db.py               # Database funktioner
│   ├── config.py           # Konfiguration
│   ├── check_meters.py     # Script til at tjekke målere
│   ├── mqtt_test.py        # Script til at teste MQTT
│   ├── requirements.txt    # Python afhængigheder
│   └── Dockerfile          # Docker konfiguration for backend
├── frontend/               # Vue.js frontend
│   ├── public/             # Statiske filer
│   ├── src/                # Kildekode
│   │   ├── components/     # Vue komponenter
│   │   ├── views/          # Vue sider
│   │   ├── router/         # Vue Router konfiguration
│   │   ├── store/          # Vuex state management
│   │   ├── services/       # API services
│   │   ├── App.vue         # Hovedapplikation
│   │   └── main.js         # Entry point
│   ├── package.json        # NPM afhængigheder
│   ├── vue.config.js       # Vue konfiguration
│   └── Dockerfile          # Docker konfiguration for frontend
├── config/                 # Konfigurationsfiler
│   └── local.env           # Miljøvariabler
├── docker-compose.yml      # Docker Compose konfiguration
└── meter_data.json         # Backup af målerdata (hvis tilgængelig)
```

## Installation

### Docker Installation

1. Download og installer Docker Desktop fra [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Sørg for at Docker kører korrekt ved at åbne en terminal og køre:
   ```
   docker --version
   ```

### Opsætning af miljøvariabler

1. Åbn filen `config/local.env` og tilpas følgende variabler efter behov:
   ```
   # Database konfiguration
   DB_PATH=/app/data/meter_database.db
   
   # MQTT konfiguration
   MQTT_BROKER=mqtt.example.com
   MQTT_PORT=1883
   MQTT_USERNAME=your_username
   MQTT_PASSWORD=your_password
   MQTT_CLIENT_ID=meter_monitor
   
   # Flask konfiguration
   FLASK_ENV=development
   ```

2. Sørg for at MQTT_BROKER, MQTT_USERNAME og MQTT_PASSWORD er korrekt indstillet til din MQTT broker.

### Bygning og opstart af containere

1. Åbn en terminal i projektets rodmappe
2. Kør følgende kommando for at bygge og starte containerne:
   ```
   docker-compose up -d
   ```
3. Vent mens Docker bygger og starter containerne
4. Når processen er færdig, kan du åbne en webbrowser og gå til:
   ```
   http://localhost:8080
   ```

## Systemarkitektur

### Backend

Backend er bygget med Python Flask og håndterer følgende:

- RESTful API for målerdata
- Socket.IO for realtidsopdateringer
- SQLite database til lagring af målerdata
- MQTT klient til kommunikation med målere

Vigtige filer:
- `app.py`: Hovedapplikationen med alle API endpoints
- `db.py`: Database funktioner til at gemme og hente målerdata
- `check_meters.py`: Script til at tjekke målerstatus
- `mqtt_test.py`: Script til at teste MQTT forbindelsen

### Frontend

Frontend er bygget med Vue.js og håndterer følgende:

- Brugergrænsefladen for måler oversigt og detaljer
- Kommunikation med backend via API og Socket.IO
- Visualisering af målerdata med grafer

Vigtige filer:
- `src/views/MeterOverview.vue`: Oversigt over alle målere
- `src/views/MeterDetail.vue`: Detaljer for en specifik måler
- `src/views/ScanMeters.vue`: Scanning efter nye målere
- `src/store/index.js`: Vuex store til state management
- `src/services/api.js`: API service til kommunikation med backend

### MQTT Integration

Systemet bruger MQTT til at kommunikere med målerne:

- Lytter til målernes status og aflæsninger
- Sender kommandoer til målerne (tænd/sluk)
- Tester MQTT forbindelsen

MQTT kommandoer:
- Tænd måler: `cmnd/obk{MAC}/Power` med payload "ON"
- Sluk måler: `cmnd/obk{MAC}/Power` med payload "OFF"

## Funktionalitet

### Måler oversigt

Måler oversigten viser alle registrerede målere med deres status og seneste aflæsning. Du kan:

- Se alle målere på én side
- Filtrere målere baseret på status (tændt/slukket)
- Søge efter målere baseret på navn eller nummer
- Klikke på en måler for at se detaljer

### Måler detaljer

Måler detaljesiden viser detaljerede oplysninger om en specifik måler:

- Målerens status og information
- Seneste aflæsninger med graf
- Dagligt forbrug med graf
- Knapper til at tænde/slukke måleren
- Knap til at teste MQTT forbindelsen
- Mulighed for at redigere målerens navn og nummer

### Scanning efter nye målere

Scan-siden giver mulighed for at scanne efter nye målere i netværket:

- Start en scanning efter nye målere
- Se resultater af scanningen
- Tilføj nye målere til systemet

## Fejlfinding

Hvis du oplever problemer med systemet, kan du prøve følgende:

1. **Genstart containerne**:
   ```
   docker-compose down
   docker-compose up -d
   ```

2. **Tjek logfiler**:
   ```
   docker-compose logs backend
   docker-compose logs frontend
   ```

3. **Tjek MQTT forbindelsen**:
   - Brug "Test MQTT" knappen på en målerdetalje side
   - Tjek om MQTT broker er tilgængelig
   - Tjek om MQTT credentials er korrekte i `config/local.env`

4. **Tjek databasen**:
   - Databasen er gemt i Docker volume og bør bevare data mellem genstarter
   - Hvis databasen er beskadiget, kan du gendanne fra `meter_data.json` hvis tilgængelig

5. **Frontend bygningsfejl**:
   - Hvis frontend ikke bygger korrekt, kan du prøve at genbygge den:
   ```
   docker-compose build --no-cache frontend
   docker-compose up -d
   ```

## Vedligeholdelse

For at holde systemet opdateret og kørende optimalt:

1. **Backup af data**:
   - Tag regelmæssige backups af databasen
   - Eksporter målerdata til JSON hvis nødvendigt

2. **Opdatering af systemet**:
   - Træk seneste ændringer fra versionsstyring (hvis brugt)
   - Genbyg containerne for at inkludere ændringer:
   ```
   docker-compose build
   docker-compose up -d
   ```

3. **Overvågning af diskplads**:
   - Databasen kan vokse over tid
   - Ryd op i gamle logfiler hvis nødvendigt

---

Dette dokument er sidst opdateret: 14. marts 2025
