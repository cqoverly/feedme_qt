from collections import namedtuple
from typing import Mapping
import requests

import feedparser

import settings


app_id = settings.APP_ID

base_url = f"http://api.digitalpodcast.com/v2r/search/?appid={app_id}"


def search(params):

    reply = requests.get(base_url, params)

    print(reply)

    return reply


def parse_search_results(results, search_words):
    
    parsed = feedparser.parse(results)
    print(parsed.entries)
    for entry in parsed.entries:
        if entry.title.find(search_words):
            print()
            print(entry.title)
            print(entry.source.href)
            print(entry.summary)




if __name__ == "__main__":

    import pprint as pp

    params = {
        "keywords": "linux",
        "format": "rss",
        "sort": "alpha",
        "results": 30}

    response = search(params)
    print(response)
    parse_search_results(response.content, params["keywords"])