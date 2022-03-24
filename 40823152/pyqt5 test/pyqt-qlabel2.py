import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel)
from PyQt5.QtGui import QFont

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('my window')
        self.setGeometry(800, 500,400, 300)
        #在 mylabel.setGeometry() 裡第 3 個引數傳入寬度，第 4 個引數傳入高度

        self.mylabel = QLabel('hello world', self)
        self.mylabel.move(150,120)
        self.mylabel.setFont(QFont('Arial', 18))
        #在 mylabel.setFont() 裡傳入 QFont，這邊示範字型為 Arial，字型大小為 18
        
        self.mylabel.setStyleSheet("background-color: yellow")
        #設定 background-color 的屬性，這邊示範黃色

if __name__ == '__main__':
    '''當 Python 檔案（模組、module）被引用的時候，檔案內的每一行都會被 Python 直譯器讀取並執行（所以 cool.py內的程式碼會被執行）
#Python直譯器執行程式碼時，有一些內建、隱含的變數，__name__就是其中之一，其意義是「模組名稱」。如果該檔案是被引用，其值會是模組名稱；但若該檔案是(透過命令列)直接執行，其值會是 __main__；'''
    app = QApplication(sys.argv)
    w = MyWidget()
    w.show()
    sys.exit(app.exec_())