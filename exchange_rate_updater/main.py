import requests
import json


def get_exchange_rate(currency):
    api_key = 'freepfILuW68dnkyVcJTNU53JfqoXEYG'
    url = f'http://api.navasan.tech/latest/?item={currency}&api_key={api_key}'
    response = requests.get(url)
    data = response.json()
    return float(data[currency]['value']) * 10

def add_exchange_rate(api_key, currency_name, price):
    url = 'http://localhost:8000/api/currency/rate/'
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        'api_key': api_key,
        'currency_name': currency_name,
        'price': price,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_data = response.json()
        if response_data.get('success'):
            exchange_rate_id = response_data.get('exchange_rate_id')
            print(f"Exchange rate added successfully. Exchange Rate ID: {exchange_rate_id}")
        else:
            print("Failed to add exchange rate.")
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Replace 'your_api_key_here', 'USD', and 100 with your desired values
    api_key = 'freepfILuW68dnkyVcJTNU53JfqoXEYG'
    currency_name = 'USD'
    price = get_exchange_rate('usd_sell')
    print(price)

    add_exchange_rate(api_key, currency_name, price)