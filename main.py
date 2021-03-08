import logging
import os
import time


import feedparser

from PySide2 import QtWidgets as qtw
from PySide2 import QtGui as qtg
from PySide2 import QtCore as qtc
from PySide2 import QtUiTools as qtu
from PySide2 import QtMultimedia as qtm
from PySide2 import Qt


import database as db
import sync


logger = logging.getLogger("app_logger")
logging.basicConfig(
    level=logging.DEBUG, format="%(process)d - %(levelname)s - %(message)s"
)

feed = "https://aphid.fireside.fm/d/1437767933/b44de5fa-47c1-4e94-bf9e-c72f8d1c8f5d/ed0eb2af-b692-4d00-996e-2eba610b17de.mp3"


class UpdateWorker(qtc.QObject):
    finished = qtc.Signal()

    def run(self):
        db.update_feeds()
        self.finished.emit()


class SettingsDialog(qtw.QInputDialog):
    def __init__(self, parent=None):
        pass


class MainWindow(qtw.QMainWindow):
    def __init__(self, ui_file, parent=None):
        super(MainWindow, self).__init__(parent)
        ui_file = qtc.QFile(ui_file)
        ui_file.open(qtc.QFile.ReadOnly)

        loader = qtu.QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        logger.info("Inteface loaded")

        self.window.closeEvent = self.closeEvent

        try:
            status = sync.get_file("podcasts.db")
            logger.info(f"Sync status: {status}")
        except Exception as e:
            logger.error(f"Unable to sync database: {e}")

        # build tables if needed
        db.build_tables()

        # create audio player
        self.player = qtm.QMediaPlayer()
        self.player.setNotifyInterval(1000)
        self.player.positionChanged.connect(self.update_time)
        self.player.stateChanged.connect(self.update_play_history)
        self.player.setVolume(50)

        # currently loaded media info
        self.podcast: str = None
        self.episode_date: str = None
        self.episode_title: str = None
        self.episode_url: str = None

        # set keyboard commands
        self.key_commands = {
            qtc.Qt.Key_Space: self.pause,
            qtc.Qt.Key_S: self.stop,
            qtc.Qt.Key_Left: self.skip_back,
            qtc.Qt.Key_Right: self.skip_forward,
            qtc.Qt.Key_VolumeMute: self.toggle_mute,
        }

        # LOAD Interface Items

        # Load Buttons and create connections
        self.btn_add_feed = self.window.findChild(qtw.QPushButton, "btn_add_feed")
        self.btn_add_feed.clicked.connect(self.add_new_feed)
        self.btn_delete_feed = self.window.findChild(qtw.QPushButton, "btn_delete_feed")
        self.btn_delete_feed.clicked.connect(self.delete_feed)
        self.btn_play = self.window.findChild(qtw.QPushButton, "btn_play")
        self.btn_play.clicked.connect(self.play)
        self.btn_stop = self.window.findChild(qtw.QPushButton, "btn_stop")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_forward = self.window.findChild(qtw.QPushButton, "btn_forward")
        self.btn_forward.clicked.connect(self.skip_forward)
        self.btn_back = self.window.findChild(qtw.QPushButton, "btn_back")
        self.btn_back.clicked.connect(self.skip_back)
        self.btn_pause = self.window.findChild(qtw.QPushButton, "btn_pause")
        self.btn_pause.clicked.connect(self.pause)
        self.btn_mute = self.window.findChild(qtw.QPushButton, "btn_mute")
        self.btn_mute.clicked.connect(self.toggle_mute)
        self.btn_settings = self.window.findChild(qtw.QPushButton, "btn_settings")
        self.btn_settings.clicked.connect(self.open_settings)

        # Labels
        self.lbl_time = self.window.findChild(qtw.QLabel, "lbl_time")

        # ListWidgets
        self.lw_episode_list = self.window.findChild(qtw.QListWidget, "lw_episode_list")
        self.lw_feed_list = self.window.findChild(qtw.QListWidget, "lw_feed_list")
        self.lw_feed_list.itemSelectionChanged.connect(self.load_episode_list)
        self.lw_episode_list.itemSelectionChanged.connect(self.load_media)
        self.lw_episode_list.itemDoubleClicked.connect(self.play)

        # Misc interface items
        self.sldr_volume = self.window.findChild(qtw.QSlider, "sldr_volume")
        self.sldr_volume.setMinimum(-10)
        self.sldr_volume.setMaximum(110)
        self.sldr_volume.setValue(50)
        self.sldr_volume.sliderMoved.connect(self.change_volume)

        # Load data into interface
        self.load_feed_list()

        self.grabKeyboard()
        self.window.show()

        # Update feeds in separate thread
        # self.update_feeds()

    def load_feed_list(self):
        logger.info("Loading feed list")
        podcasts = sorted(db.get_podcasts())
        try:
            self.lw_feed_list.clear()
            self.lw_feed_list.addItems(podcasts)
            logger.info("Podcast list loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load podcast list:\n{e}")

    def load_episode_list(self):
        feed = self.lw_feed_list.selectedItems()[0].text()
        episodes = db.get_episodes(feed)
        ep_dates = episodes.keys()
        self.lw_episode_list.clear()
        self.lw_episode_list.addItems(ep_dates)

    def load_media(self):
        feed: str = self.lw_feed_list.selectedItems()[0].text()
        episodes: dict = db.get_episodes(feed)
        episode: str = self.lw_episode_list.selectedItems()[0].text().strip()
        url: str = episodes[episode]["url"]
        # find if episode has been played before, and get position
        previous_episode_history = db.get_episode_history(url)
        position = 0
        if previous_episode_history:
            position = previous_episode_history[1]
            print(f"Last position was: {position}")
        media_url = qtc.QUrl(url)
        self.player.setMedia(media_url)
        self.player.setPosition(position)

    def change_volume(self):
        value = self.sldr_volume.value()
        linear_volume = qtm.QAudio.convertVolume(
            (value / 100),
            qtm.QAudio.LogarithmicVolumeScale,
            qtm.QAudio.LinearVolumeScale,
        )
        self.player.setVolume(round(linear_volume * 100))
        print(self.player.volume())

    def add_new_feed(self):

        add_dialog = qtw.QInputDialog()
        self.releaseKeyboard()
        feed_url, ok = add_dialog.getText(
            self, "Enter Feed URL", "Feed Url:", qtw.QLineEdit.Normal, ""
        )

        try:
            urls = db.get_podcast_urls()
            valid_feed = test_feed(feed_url)
            if not valid_feed or feed_url in urls:
                logger.error(f"{feed_url} is ain invalid feed.")
            else:  # if no feeds are in database
                logger.info(f"{feed_url} is a valid feed.")
                db.parse_xmls_to_database(feed_url)
            self.load_feed_list()
        except Exception as e:
            logger.error(f"Invalid feed entered:\n{e}")
        self.grabKeyboard()

    def delete_feed(self):
        print("Delete feed")

    def play(self):
        self.load_media()
        self.player.play()

    def pause(self):
        if self.player.state() == qtm.QMediaPlayer.State.PlayingState:
            self.player.pause()
        elif self.player.state() == qtm.QMediaPlayer.State.PausedState:
            self.player.play()
        else:
            pass

    def stop(self):
        position = self.player.position()
        self.update_play_history()
        if self.player.state() == qtm.QMediaPlayer.State.PlayingState:
            self.player.stop()
            self.player.setPosition(position)

    def skip_forward(self):
        self.player.setPosition(self.player.position() + 15000)

    def skip_back(self):
        self.player.setPosition(self.player.position() - 15000)

    def toggle_mute(self):
        if self.player.isMuted():
            self.player.setMuted(False)
        else:
            self.player.setMuted(True)
        print("Toggling mute")

    def keyPressEvent(self, event):
        key = event.key()
        commands = self.key_commands.keys()
        if key == qtc.Qt.Key_Q:
            self.closing_handler()
            sys.exit()
        elif key in commands:
            self.key_commands[event.key()]()
        else:
            print(key)

    def update_time(self):
        duration = self.player.duration() / 1000
        d_min = str(round(duration // 60)).zfill(2)
        d_sec = str(round(duration % 60)).zfill(2)
        current_time = self.player.position() / 1000
        curr_min = str(round(current_time // 60)).zfill(2)
        curr_sec = str(round(current_time % 60)).zfill(2)
        self.lbl_time.setText(f"Current time: {curr_min}:{curr_sec} / {d_min}:{d_sec}")

    def update_feeds(self):
        self.update_thread = qtc.QThread()
        self.update_worker = UpdateWorker()
        self.update_worker.moveToThread(self.update_thread)
        self.update_thread.started.connect(self.update_worker.run)
        self.update_worker.finished.connect(self.update_thread.quit)
        self.update_worker.finished.connect(self.update_worker.deleteLater)
        self.update_thread.finished.connect(self.update_thread.deleteLater)

        self.update_thread.start()

    def update_play_history(self):
        p = self.player
        if p.state() == qtm.QMediaPlayer.StoppedState:
            pass
        elif p.position() < 1000:
            pass
        else:
            print(f"Update play history: {p.position()}")
            print(p.media().canonicalUrl().url())
            db.update_tbl_episodes_played(p.media().canonicalUrl().url(), p.position())

    def open_settings(self):
        settings, ok = qtw.QInputDialog()
        print("Settings")

    def closeEvent(self, event: qtg.QCloseEvent) -> None:
        print("Come on, man!")
        return super().closeEvent(event)

    def closing_handler(self):
        logger.info(f"Preparing to close")
        sync.push_file("podcasts.db")


def test_feed(url):
    test_feed = feedparser.parse(url)
    episodes = test_feed.entries
    if not episodes:
        return False
    else:
        return True


if __name__ == "__main__":
    import sys

    qtc.QCoreApplication.setAttribute(qtc.Qt.AA_ShareOpenGLContexts)
    app = qtw.QApplication(sys.argv)
    MainWindow = MainWindow("player.ui")
    app.aboutToQuit.connect(MainWindow.closing_handler)
    sys.exit(app.exec_())
