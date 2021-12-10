import time

import requests
from bs4 import BeautifulSoup as bs


QUERY = "EuroCrops: A Pan-European Dataset for Time Series Crop Type Classification"
BASE_URL = (
    f"https://scholar.google.com/scholar?q={QUERY}&ie=UTF-8&oe=UTF-8&hl=en&btnG=Search"
)


INTERVAL_S = 1


def get_latest_citation_count(url: str) -> int:
    """
    Fetches the most recent citation count for the given paper

    Parameters
    ----------
    url
        URL from which to retrieve the cite count. Must countain 'Cited by' as part of the
        html response

    Returns
    -------
    int
        number of citations
    """
    with requests.Session() as r:
        res = r.get(url)
        soup = bs(res.content, 'html.parser')
        cite_count = (
            soup.select_one('a:-soup-contains("Cited by")').text 
            if soup.select_one('a:-soup-contains("Cited by")') is not None 
            else '0'
        )
    return int(cite_count.split(' ')[-1])


def start_local_polling_for_citations(url: str, interval_sec: int) -> None:
    """
    Starts regularly polling the url for changes in citation count and prints to stdout

    Parameters
    ----------
    url
        URL from which to retrieve the cite count. Must contain 'Cited by' as part of the
        html response

    interval_sec
        interval in seconds between polling attempts
    """
    c0 = get_latest_citation_count(url)
    print(f"Total number of citations at start: {c0}")
    while True:
        c1 = get_latest_citation_count(url)
        time.sleep(interval_sec)
        if c1 > c0:
            print(
                f"THERE'S BEEN MORE CITATIONS!!\n"
                f"You've been cited by: {c1}"
            )
            c1 = c0


if __name__ == "__main__":
    print("Starting local poll...")
    start_polling_for_citations(BASE_URL, INTERVAL_S)
