import httpx
import os
from dotenv import load_dotenv

load_dotenv()

M2M_TOKEN = os.getenv("M2M_TOKEN")
url = "https://goteamup.com/api/v2/reports/attendances.grouped/data"

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {M2M_TOKEN}",
    "TeamUp-Request-Mode": "provider"
}

# We omit the status parameter completely to avoid empty server filtering
params = [
    ("columns", "customer"),
    ("start_date", "2010-01-01"),  # Adjust to any date before your business opened
    ("end_date", "2030-12-31")     # Captures all historical logs up to the future cutoff
]

with httpx.Client() as client:
    response = client.get(url, headers=headers, params=params, timeout=30.0)

if response.status_code != 200:
    print(f"Server Error Status: {response.status_code}")
    print(f"Raw Server Message: '{response.text}'")
else:
    report_data = response.json()
    rows = report_data.get("rows", [])
    
    leaderboard = []
    for row in rows:
        # TeamUp stores grouped customer dimensions inside a nested object dictionary
        customer_obj = row.get("customer", {})
        
        # Fallback to direct string keys in case the engine flattens them
        id = customer_obj.get("id") or row.get("customer.id") or "ID Not Found"
        name = customer_obj.get("name") or row.get("customer.name") or "Unknown Customer"
        email = customer_obj.get("email") or row.get("customer.email") or "No Email Provided"
        count = row.get("count", 0)
        
        leaderboard.append({"id": id, "name": name, "email": email, "count": count})
    
    # Sort the list inline based on the attendance count field (highest first)
    leaderboard.sort(key=lambda x: x["count"], reverse=True)
    
    print("\n==========================================")
    print("      LIFETIME CUSTOMER LEADERBOARD       ")
    print("==========================================")
    for rank, client_profile in enumerate(leaderboard, start=1):
        print(f"{rank:2d}. {client_profile['name']:<25} | {client_profile['count']:3d} visits ({client_profile['email']})")
