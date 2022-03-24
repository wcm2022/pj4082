import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QLineEdit,
                             QLabel, QPushButton)

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('my window')
        self.setGeometry(50, 50, 240, 80)

        gridlayout = QGridLayout()
        #ui自動排版
        self.setLayout(gridlayout)

        self.mylabel = QLabel('Name:', self)
        gridlayout.addWidget(self.mylabel, 0, 0)
        #(座標第0排，第1列)
        self.mylineedit = QLineEdit(self)
        gridlayout.addWidget(self.mylineedit, 0, 1)

        self.mybutton = QPushButton('button', self)
        gridlayout.addWidget(self.mybutton, 1, 0, 1, 2)
        #self.mybutton(x,x,1,2)意思為水平橫跨1網格單位
        self.mybutton.clicked.connect(self.onButtonClick)

    def onButtonClick(self):
        #print(self.mylineedit.text())
        if self.mylineedit.text() != '':
            self.mybutton.setText(self.mylineedit.text())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MyWidget()
    w.show()
    sys.exit(app.exec_())