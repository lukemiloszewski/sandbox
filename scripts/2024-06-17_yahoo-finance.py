import re
import time
from datetime import datetime

import pandas as pd
import requests


def load_price_data(stock, interval="1d", day_begin="01-03-2019", day_end="28-03-2019"):
    day_begin_unix = _convert_to_unix(day_begin)
    day_end_unix = _convert_to_unix(day_end)
    header, crumb, cookies = _get_crumbs_and_cookies(stock)

    print(header, crumb, cookies)

    url = f"https://query1.finance.yahoo.com/v7/finance/download/{stock}?period1={day_begin_unix}&period2={day_end_unix}&interval={interval}&events=history&crumb={crumb}"
    response_raw = requests.get(url, headers=header, cookies=cookies)
    response = response_raw.text.split("\n")[:-1]

    rv = pd.DataFrame([sub.split(",") for sub in response])
    print(rv)
    return rv


def _get_crumbs_and_cookies(stock):
    # url = "https://query2.finance.yahoo.com/v1/test/getcrumb"  # doesn't work consistently
    url = f"https://finance.yahoo.com/quote/{stock}/history"
    header = {
        "Connection": "keep-alive",
        "Expires": "-1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36",
    }

    while True:
        response = requests.get(url, headers=header)
        if response.status_code != 200:
            raise ConnectionError(f"Failed to retrieve data: HTTP {response.status_code}")

        crumb_pattern = r'"crumb":"([a-zA-Z0-9]*)"'
        crumb_match = re.search(crumb_pattern, response.text)

        cookies = response.cookies

        print(crumb_match, cookies)

        if crumb_match:
            crumb = crumb_match.group(1)
            return header, crumb, cookies

        time.sleep(1)


def _convert_to_unix(date):
    datum = datetime.strptime(date, "%d-%m-%Y")
    return int(time.mktime(datum.timetuple()))


if __name__ == "__main__":
    load_price_data("MSFT")
