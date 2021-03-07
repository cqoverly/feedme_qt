import base64
from ftplib import FTP
import logging
from pathlib import Path
from typing import Type

import settings

logger = logging.getLogger("app_logger")
logging.basicConfig(
    level=logging.DEBUG, format="%(process)d - %(levelname)s - %(message)s"
)

server = settings.FTP_SERVER
user = settings.USER
passwd = base64.b64decode(settings.PASSWD).decode()

remote_dir_path = '~/Documents/'

file = 'podcasts.db'

def sync_file(file_to_sync):
    ftp = FTP(server)
    remote_file_path = Path(remote_dir_path).joinpath(file_to_sync)
    logger.info(f"Attempting ftp connection to {remote_file_path}")
    try:
        ftp.login(user=user, passwd=passwd)
        logger.info(f"ftp connect SUCCESS:  {ftp.welcome}")
    except TypeError as e:
        logger.error(f"ftp connection FAILED: {e}")
    finally:
        ftp.quit()
        logger.info("ftp connection closed")






if __name__ == "__main__":

    sync_file(file)
