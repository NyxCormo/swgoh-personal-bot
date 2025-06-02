import requests
from collections import Counter
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIG ---

BASE_URL = "http://localhost:3000"
ALLY_CODE = "659735537"

SERVICE_ACCOUNT_FILE = "swgoh-sheet-bot-30feef5191ac.json"
SPREADSHEET_NAME = "SWGoH Farming Plan"
STATS_SHEET = "Stats"
CHARACTERS_SHEET = "Characters"

# --- UTILS ---

def get_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    return gspread.authorize(creds)

def get_or_create_sheet(spreadsheet, name, rows=1000, cols=20):
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=rows, cols=cols)

# --- CORE ---

def fetch_player(ally_code):
    print("Récupération des données du joueur...")
    url = f"{BASE_URL}/player"
    payload = {"payload": {"allyCode": ally_code}}
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()

def analyze_units(data):
    units = data.get("rosterUnit", [])
    total = len(units)

    rarity = Counter()
    gear = Counter()
    levels = []
    gears = []
    names = Counter()

    for u in units:
        rarity[u.get("currentRarity", 0)] += 1
        gear[u.get("currentTier", 0)] += 1
        levels.append(u.get("currentLevel", 0))
        gears.append(u.get("currentTier", 0))
        names[u.get("definitionId", "UNKNOWN")] += 1

    avg_level = round(sum(levels)/total, 2) if total else 0
    avg_gear = round(sum(gears)/total, 2) if total else 0

    return {
        "total_units": total,
        "rarity_distribution": dict(sorted(rarity.items())),
        "gear_distribution": dict(sorted(gear.items())),
        "average_level": avg_level,
        "average_gear": avg_gear,
        "top_units": dict(names.most_common(10))
    }

def update_stats_sheet(stats):
    client = get_client()
    sheet = client.open(SPREADSHEET_NAME).worksheet(STATS_SHEET)
    sheet.clear()

    data = [
        ["Statistique", "Valeur"],
        ["Nombre total d'unités", stats["total_units"]],
        ["Niveau moyen des unités", stats["average_level"]],
        ["Gear moyen des unités", stats["average_gear"]],
        [],
        ["Rareté (étoiles)", "Nombre d’unités"],
    ]

    data += [[str(r), c] for r, c in stats["rarity_distribution"].items()]
    data.append([])
    data.append(["Gear (niveau d'équipement)", "Nombre d’unités"])
    data += [[str(g), c] for g, c in stats["gear_distribution"].items()]
    data.append([])
    data.append(["Unités les plus fréquentes", "Nombre d’unités"])
    data += [[n, c] for n, c in stats["top_units"].items()]

    sheet.update("A1", data)
    print("Stats mises à jour dans la feuille Stats.")

def update_characters_sheet(data):
    client = get_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    sheet = get_or_create_sheet(spreadsheet, CHARACTERS_SHEET)
    sheet.clear()

    headers = [
        "ID", "DefinitionId", "Name", "Stars", "Level", "XP", "Gear Level",
        "Relic Tier", "Skills", "Equipment Slots"
    ]
    rows = [headers]

    for u in data.get("rosterUnit", []):
        unit_id = u.get("id", "")
        def_id = u.get("definitionId", "")
        name = def_id.split(":")[0] if ":" in def_id else def_id
        stars = u.get("currentRarity", 0)
        level = u.get("currentLevel", 0)
        xp = u.get("currentXp", 0)
        gear = u.get("currentTier", 0)
        relic = u.get("relic")
        relic_tier = relic.get("currentTier") if relic else 0

        skills = u.get("skill", [])
        skills_str = ", ".join(f"{s.get('id', '')}({s.get('tier', '')})" for s in skills)

        equipment = u.get("equipment", [])
        equipment_str = ", ".join(f"{e.get('equipmentId', '')}[{e.get('slot', '')}]" for e in equipment)

        row = [
            unit_id, def_id, name, stars, level, xp, gear,
            relic_tier, skills_str, equipment_str
        ]

        rows.append(row)
        print(f"Prêt à écrire '{name}'...")

    sheet.update(f"A1:J{len(rows)}", rows)
    print(f"Feuille '{CHARACTERS_SHEET}' mise à jour avec {len(rows)-1} unités.")

def main():
    data = fetch_player(ALLY_CODE)
    stats = analyze_units(data)
    update_stats_sheet(stats)
    update_characters_sheet(data)

if __name__ == "__main__":
    main()
