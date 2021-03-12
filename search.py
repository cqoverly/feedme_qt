from collections import namedtuple
from typing import Mapping
import requests

import feedparser

import settings


search_app_id = settings.SEARCH_APP_ID

base_url = f"http://api.digitalpodcast.com/v2r/search/?appid={search_app_id}"


def search(keywords):

    params = {"keywords": keywords, "format": "rss", "sort": "rel", "results": 10}

    reply = requests.get(base_url, params)

    print(reply)

    return reply


def parse_search_results(results, search_words):

    parsed = feedparser.parse(results)
    for entry in parsed.entries:
        print()
        print(entry.title)
        print(entry.source.href)
        print(entry.summary)


if __name__ == "__main__":

    import pprint as pp

    search_words = input("Enter title words to search: ")

    response = search(search_words)
    print(response)
    parse_search_results(response.content, search_words)
