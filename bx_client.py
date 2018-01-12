from decimal import Decimal
import requests


def recent_trades():
    res = requests.get('https://bx.in.th/api/trade/?pairing=21')
    data = res.json()
    trades = data['trades']
    avg_rate = sum(Decimal(x['rate']) for x in trades) / len(trades)
    return avg_rate
