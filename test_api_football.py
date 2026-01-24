import requests

API_KEY = "8f5493409b6b1cfe172c12823b61589a"

url = "https://v3.football.api-sports.io/status"

headers = {
    "x-apisports-key": API_KEY
}

response = requests.get(url, headers=headers)

print("Status code:", response.status_code)
print("Response:")
print(response.json())
