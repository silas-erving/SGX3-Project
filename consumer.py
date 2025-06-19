import requests

response = requests.get("http://35.206.76.195:8030/head?count=10")

# Check to see if the request worked
print(response.status_code)     # Should print 200 if OK
print(response.headers)         # Metadata about the response


#view our json data
data = response.json()
print(data)

