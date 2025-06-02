import requests
import json

BASE_URL = "http://localhost:3000"
ALLY_CODE = "659735537"

def fetch_player_data(ally_code):
    url = f"{BASE_URL}/player"
    payload = {
        "payload": {
            "allyCode": ally_code
        }
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def save_to_file(data, filename="data.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Données sauvegardées dans {filename}")

def main():
    data = fetch_player_data(ALLY_CODE)
    save_to_file(data)

if __name__ == "__main__":
    main()
