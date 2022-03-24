#https://shengyu7697.github.io/python-pyqt-tutorial/
import sys
from PyQt5.QtWidgets import (QApplication, QWidget)
#QApplication用來管理Qt GUI應用程式的控制與主要設定
#MyWidge繼承了QWidget
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('hello world')
        self.setGeometry(150, 150, 600, 550)
        #視窗位置與大小(x,y,寬度,高度)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MyWidget()
    w.show()
    
    sys.exit(app.exec_())