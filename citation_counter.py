import time

import requests
from bs4 import BeautifulSoup as bs


QUERY = "EuroCrops: A Pan-European Dataset for Time Series Crop Type Classification"
BASE_URL = (
    f"https://scholar.google.com/scholar?q={QUERY}&ie=UTF-8&oe=UTF-8&hl=en&btnG=Search"
)


INTERVAL_S = 1


def get_latest_citation_count() -> int:
    with requests.Session() as r:
        res = r.get(BASE_URL)
        soup = bs(res.content, 'html.parser')
        cite_count = (
            soup.select_one('a:-soup-contains("Cited by")').text 
            if soup.select_one('a:-soup-contains("Cited by")') is not None 
            else '-999'
        )
    return int(cite_count.split(' ')[-1])


def start_polling_for_citations(interval_sec):
    c0 = get_latest_citation_count()
    print(f"Total number of citations at start: {c0}")
    while True:
        c1 = get_latest_citation_count()
        time.sleep(interval_sec)
        if c1 > c0:
            print(
                f"THERE'S BEEN MORE CITATIONS!!\n"
                f"You've been cited by: {c1}"
            )
            c1 = c0
        print("Heartbeat")


if __name__ == "__main__":
    start_polling_for_citations(interval_sec=INTERVAL_S)
