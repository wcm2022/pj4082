from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from QLed import QLed
import cv2
from UI import Ui_MainWindow

# child threaded script: 
#simExtRemoteApiStart(19999)
 

class MainWindow_controller(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__() 
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_control()

    def setup_control(self):
        self.gray_path = 'gray.png'
        self.display_img()
        self.green_path = 'green.png'
        self.Light_contorl()
    def display_img(self):
        self.img = cv2.imread(self.gray_path)
        height, width, channel = self.img.shape
        bytesPerline = 3 * width
        self.qimg = QImage(self.img, width, height, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        self.ui.P.setPixmap(QPixmap.fromImage(self.qimg))
        self.ui.E.setPixmap(QPixmap.fromImage(self.qimg))
        self.ui.X.setPixmap(QPixmap.fromImage(self.qimg))
        self.ui.Y.setPixmap(QPixmap.fromImage(self.qimg))
        self.ui.Z.setPixmap(QPixmap.fromImage(self.qimg))
    def Light_contorl(self):
        self.green_img = cv2.imread(self.green_path)
        height, width, channel = self.green_img.shape
        bytesPerline = 3 * width
        self.qimg = QImage(self.green_img, width, height, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        self.ui.P.setPixmap(QPixmap.fromImage(self.qimg))
        