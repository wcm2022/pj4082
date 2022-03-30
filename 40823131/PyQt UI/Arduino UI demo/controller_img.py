from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from QLed import QLed
import cv2

from UI import Ui_MainWindow

class MainWindow_controller(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__() 
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_control()

    def setup_control(self):
        self.img_path = 'arduino.png'
        self.display_img()
        self.led_img_path = 'green light icon.png'
        self.led_img()
        
    def display_img(self):
        self.img = cv2.imread(self.img_path)
        height, width, channel = self.img.shape
        bytesPerline = 3 * width
        self.qimg = QImage(self.img, width, height, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        self.ui.label.setPixmap(QPixmap.fromImage(self.qimg))
    def led_img(self):
        self.led_img = cv2.imread(self.led_img_path)
        height, width, channel = self.led_img.shape
        bytesPerline = 3 * width
        self.led_qimg = QImage(self.led_img, width, height, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        self.ui.label_1.setPixmap(QPixmap.fromImage(self.led_qimg))
