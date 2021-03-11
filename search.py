from collections import namedtuple
from typing import Mapping
import requests

import settings


app_id = settings.APP_ID

base_url = f"http://api.digitalpodcast.com/v2r/search/?appid={app_id}"


def search(params):

    reply = requests.get(base_url, params)

    print(reply)

    return reply




if __name__ == "__main__":

    params = {"keywords": "linux", "format": "rss"}

    response = search(params)
    print(response.encoding)
    print()
    print(response.content)