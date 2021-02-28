import logging
import os

from PySide2 import QtWidgets as qtw
from PySide2 import QtGui as qtg
from PySide2 import QtCore as qtc
from PySide2 import QtUiTools as qtu
from PySide2 import Qt


logger = logging.getLogger("app_logger")
logging.basicConfig(
    level=logging.DEBUG, format="%(process)d - %(levelname)s - %(message)s"
)


class MainWindow(qtw.QMainWindow):
    def __init__(self, ui_file, parent=None):
        super(MainWindow, self).__init__(parent)
        ui_file = qtc.QFile(ui_file)
        ui_file.open(qtc.QFile.ReadOnly)

        loader = qtu.QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()
        logger.info("Inteface loaded")

        # set keyboard commands
        self.key_commands = {
                qtc.Qt.Key_Space: self.pause,
                qtc.Qt.Key_S: self.stop,
                qtc.Qt.Key_Left: self.skip_back,
                qtc.Qt.Key_Right: self.skip_forward,
                qtc.Qt.Key_VolumeMute: self.toggle_mute
        }


        # LOAD Interface Items

        # Load Buttons and create connections
        self.btn_add_feed = self.window.findChild(qtw.QPushButton, "btn_add_feed")
        self.btn_add_feed.clicked.connect(self.add_feed)
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
        # Labels
        self.lbl_time = self.window.findChild(qtw.QLabel, "lbl_time")

        # ListWidgets
        self.lw_episode_list = self.window.findChild(qtw.QListWidget, "")
        self.lw_episode_list = self.window.findChild(qtw.QListWidget, "lw_episode_list")

        self.grabKeyboard()
        self.window.show()

    def add_feed(self):
        print("Adding feed")

    def play(self):
        print("Playing")

    def pause(self):
        print("Paused")
    def stop(self):
        print("Stopped")

    def skip_forward(self):
        print("Skipping forward")

    def skip_back(self):
        print("Skipping back")

    def toggle_mute(self):
        print("Toggling mute")

    def keyPressEvent(self, event):
        key = event.key()
        commands = self.key_commands.keys()
        if key == qtc.Qt.Key_Q:
            sys.exit()
        elif key in commands:
            self.key_commands[event.key()]()
        else:
            print(key)


if __name__ == "__main__":
    import sys

    qtc.QCoreApplication.setAttribute(qtc.Qt.AA_ShareOpenGLContexts)
    app = qtw.QApplication(sys.argv)
    MainWindow = MainWindow("player.ui")
    sys.exit(app.exec_())
