from config import Config
from clients.teamup import TeamUpClient

Config.ensure_token()

client = TeamUpClient(Config.M2M_TOKEN)

attendances = client.get_attendances()

print(attendances)