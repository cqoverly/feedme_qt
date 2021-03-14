import sqlite3
import threading
import feedparser
import json
import logging
from pathlib import Path

import settings


logger = logging.getLogger("app_logger")
logging.basicConfig(
    level=logging.DEBUG, format="%(process)d - %(levelname)s - %(message)s"
)


build_tbl_podcast_query = """
        CREATE TABLE IF NOT EXISTS tbl_podcast (
            podcast_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(64),
            url VARCHAR(256),
            episodes_json TEXT
        )
    """

build_tbl_played_episodes = """
        CREATE TABLE IF NOT EXISTS tbl_episodes_played (
            episode_url TEXT PRIMARY KEY,
            last_time INTEGER NOT NULL
        )
    """

build_tbl_user_settings = """
        CREATE TABLE IF NOT EXISTS tbl_user_settings (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            server TEXT
        )
"""

add_new_play_history_query = """
        INSERT INTO tbl_episodes_played
        VALUES (?, ?)
    """

update_play_history_query = """
        UPDATE tbl_episodes_played
        SET last_time = ?
        WHERE episode_url = ?
    """

get_episode_history_query = """
        SELECT *
        FROM tbl_episodes_played
        WHERE episode_url = ?
    """

get_feed_urls_query = """
        SELECT url
        FROM tbl_podcast
    """

update_user_settings_query = """
        UPDATE tbl_user_settings 
        SET
            username = ?
            password = ?
            server = ?
        WHERE user_id = ?
"""

insert_new_user_settings_query = """
        INSERT INTO tbl_user_settings (username, password, server)
        VALUES (?,?,?)
"""

all_feed_xmls = []
feeds_in_db = []

# generate connection to the database
conn = None  # holder for db connection


def get_conn():
    conn = sqlite3.connect("podcasts.db")
    return conn


def db_check():
    if not Path("podcasts.db").is_file():
        build_tables()


def build_tables():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(build_tbl_podcast_query)
    cur.execute(build_tbl_played_episodes)
    cur.execute(build_tbl_user_settings)
    conn.commit()
    return True


# def get_stored_urls():
#     conn = get_conn()
#     cur = conn.cursor()
#     url_data = cur.execute(get_feed_urls_query)
#     feeds_in_db = [url for url in url_data]
#     conn.close()
#     return feeds_in_db


def parse_xmls_to_database(feed_url):
    feeds_in_db = get_podcast_urls()
    d = feedparser.parse(feed_url)
    title = d.feed.title
    podcast_url = d.url
    episodes = d.entries[:12]
    # parse episodes into list of episodes dicts
    parsed_episodes = {}
    for episode in episodes:
        ep_date = episode.published
        parsed_episodes[ep_date] = {}
        parsed_episodes[ep_date]["title"] = episode.title
        ep_url = ""
        for enc in episode.enclosures:
            if enc["type"].startswith("audio/"):
                ep_url = enc["url"]
                break
        parsed_episodes[ep_date]["url"] = ep_url
    episodes_json = json.dumps(parsed_episodes)
    conn = get_conn()
    cur = conn.cursor()
    if podcast_url in feeds_in_db:
        # update episodes list: refactor to check list first?
        sql = """
            UPDATE tbl_podcast
            SET episodes_json = ?
            WHERE url = ?
        """
        cur.execute(sql, (episodes_json, podcast_url))
        conn.commit()
    else:
        sql = """
            INSERT INTO tbl_podcast (title, url, episodes_json)
            VALUES (?,?,?)
        """
        cur = conn.cursor()
        cur.execute(sql, (title, podcast_url, episodes_json))
        conn.commit()
    conn.close()


def get_podcasts():
    podcasts_sql = """
            SELECT title
            FROM tbl_podcast
            ORDER BY title
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(podcasts_sql)
    podcasts: list = [p[0] for p in cur.fetchall()]
    return podcasts


def get_podcast_urls():
    get_urls_sql = """
            SELECT url
            FROM tbl_podcast
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(get_urls_sql)
    urls = [u[0] for u in cur]
    return urls


def get_episodes(podcast_title):
    epidodes_sql = """
            SELECT episodes_json
            FROM tbl_podcast
            WHERE title = ?
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(epidodes_sql, (podcast_title,))
    episodes_data: str = cur.fetchone()[0]
    episodes_info: dict = json.loads(episodes_data)
    return episodes_info


def get_episode_history(url):
    sql = get_episode_history_query
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, (url,))
    history = cur.fetchone()
    return(history)


def update_tbl_episodes_played(
        url,
        last_time
    ):

    # check if episode is already entered
    sql = get_episode_history_query
    conn = get_conn()
    cur = conn.cursor()
    cur .execute(sql, (url,))
    history = cur.fetchone()
    if history:
        # update current record.
        params = (last_time, url)
        sql = update_play_history_query
        cur.execute(sql, params)
        conn.commit()
    else:
        # create new record in table
        params = (
            url,
            last_time
        )
        sql = add_new_play_history_query
        cur.execute(sql, params)
        conn.commit()


def update_feeds():
    db_check()
    feeds_in_db = get_podcast_urls()
    # feeds = []
    # with open("feeds.json", "r") as f:
    #     feeds = json.loads(f.read())
    #     print(feeds)
    for feed in feeds_in_db:
        thread = threading.Thread(target=parse_xmls_to_database, args=(feed,))
        thread.start()
        thread.join()
    # for xml in all_feed_xmls:
    #     parse_xmls_to_database(xml, feed_url)


def update_user_settings(username, password, server):
    sql = update_user_settings_query
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM tbl_user_settings;")
    try:
        user_id = cur.fetchone()[0]
        params = (username, password, server, user_id)
        cur.execute(sql, params)
    except TypeError as e:
        sql = insert_new_user_settings_query
        params = (username, password, server)
        cur.execute(sql, params)
    finally:
        conn.commit()
        conn.close()
    


if __name__ == "__main__":
    update_feeds()
