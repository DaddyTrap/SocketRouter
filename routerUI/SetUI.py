# -*- coding: utf-8 -*-

import sys

from PyQt5.QtWidgets import QApplication , QMainWindow

from routerui import *

 
if __name__ == '__main__':

    class CoperQt(QtWidgets.QMainWindow,Ui_MainWindow):#创建一个Qt对象
    #这里的第一个变量是你该窗口的类型，第二个是该窗口对象。
    #这里是主窗口类型。所以设置成当QtWidgets.QMainWindow。
    #你的窗口是一个会话框时你需要设置成:QtWidgets.QDialog
        def __init__(self):
            QtWidgets.QMainWindow.__init__(self)  # 创建主界面对象
            Ui_MainWindow.__init__(self)#主界面对象初始化
            self.setupUi(self)  #配置主界面对象

    if __name__ == "__main__":
        app = QtWidgets.QApplication(sys.argv)
        window = CoperQt()#创建QT对象
        # window.setTrafficText('Hello World')
        window.show()#QT对象显示
        sys.exit(app.exec_())

