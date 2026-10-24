import httpx
from src.config import Config

class TeamUpClient:
    def __init__(self, m2m_token: str = None):
        self.token = m2m_token or Config.M2M_TOKEN
        self.url = "https://goteamup.com/api/v2/reports/attendances.grouped/data"
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def get_attendances(self):
        next_url = self.url
        params = [
            ("columns", "customer"),
            ("attendance_status[]", "attended")
        ]
        attendances = []

        with httpx.Client() as client:
            while next_url:
                response = client.get(
                    url=next_url, 
                    headers=self.headers, 
                    params=params if next_url == self.url else None, 
                    timeout=30.0
                    )
                if response.status_code != 200:
                        print(f"TeamUp API Error ({response.status_code}): {response.text}")
                response.raise_for_status()

                data = response.json()
                # print(data)
                rows = data.get("rows", [])
                if not rows:
                    break
                
                for row in rows:
                    customer_obj = row.get("customer", {})
                    id = customer_obj.get("id") or row.get("customer.id") or "ID Not Found"
                    name = customer_obj.get("name") or row.get("customer.name") or "Unknown Customer"
                    email = customer_obj.get("email") or row.get("customer.email") or "No Email Associated"
                    count = row.get("count", 0)

                    attendances.append({"ID": id, "Customer": name, "Email": email, "Attendances": count})

                next_url = data.get("next")
        return attendances

if __name__ == "__main__":
     client = TeamUpClient()
     attendances = client.get_attendances()
     print(attendances)
