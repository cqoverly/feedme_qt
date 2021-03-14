import base64
from ftplib import FTP, FTP_TLS
import logging
import os
from pathlib import Path
from ssl import SSLContext
from typing import Type

import settings
import database as db

logger = logging.getLogger("app_logger")
logging.basicConfig(
    level=logging.DEBUG, format="%(process)d - %(levelname)s - %(message)s"
)


user_info = db.get_user_settings()
try:
    settings = user_info
    print(settings)
    user, passwd, server = settings
    passwd = base64.b64decode(passwd).decode()
except TypeError as e:
    user, passwd, server = (None, None, None)


# server = settings.FTP_SERVER
# user = settings.USER
# passwd = base64.b64decode(settings.PASSWD).decode()

remote_dir_path = "files"


def get_file(file_to_sync):
    ftp = FTP_TLS(server)
    logger.info(f"Attempting ftp connection to {server}")
    try:
        ftp.login(user=user, passwd=passwd)
        ftp.prot_p()
        logger.info(f"ftp connect SUCCESS:  {ftp.welcome}")
        ftp.cwd(remote_dir_path)
        with open(file_to_sync, "wb") as localfile:
            status = ftp.retrbinary(f"RETR {file_to_sync}", localfile.write)
            logger.info(f"Attempting to download {file_to_sync}: {status}")

    except Exception as e:
        logger.error(f"ftp connection FAILED: {e}")
    finally:
        ftp.quit()
        logger.info("ftp connection closed")


def push_file(file_to_sync):
    ftp = FTP_TLS(server)
    logger.info(f"Attempting ftp connection to {server}")
    try:
        ftp.login(user=user, passwd=passwd)
        ftp.prot_p()
        logger.info(f"ftp connect SUCCESS:  {ftp.welcome}")
        ftp.cwd(remote_dir_path)
        with open(file_to_sync, "rb") as localfile:
            status = ftp.storbinary(f"STOR {file_to_sync}", localfile)
            logger.info(f"Attempting to updload {file_to_sync}: {status}")

    except Exception as e:
        logger.error(f"ftp connection FAILED: {e}")
    finally:
        ftp.quit()
        logger.info("ftp connection closed")


if __name__ == "__main__":

    push_file("podcasts.db")
    # get_file('podcasts_copy.db')
