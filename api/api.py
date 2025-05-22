import httpx


async def get_binance_price(symbol: str):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

        if response.status_code == 200:
            data = response.json()
            price = float(data["lastPrice"])
            change_percent = float(data["priceChangePercent"])
            return price, change_percent
        else:
            print("❌ Помилка при запиті:", response.status_code)
            return None
