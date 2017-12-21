# -*- coding: utf-8 -*-

import sys

from PyQt5.QtWidgets import QApplication , QMainWindow

import CentralUI
import routerui
 
if __name__ == '__main__':

    if len(sys.argv) <= 1:
        print("One argument representing the node mode is needed.")
        sys.exit(0)
    if len(sys.argv) > 2:
        test_type = sys.argv[2]

    mode = sys.argv[1]


    if mode == "CSL":
        class CoperQt(QMainWindow,CentralUI.Ui_MainWindow):#创建一个Qt对象
        #这里的第一个变量是你该窗口的类型，第二个是该窗口对象。
        #这里是主窗口类型。所以设置成当QtWidgets.QMainWindow。
        #你的窗口是一个会话框时你需要设置成:QtWidgets.QDialog
            def __init__(self):
                QMainWindow.__init__(self)  # 创建主界面对象
                CentralUI.Ui_MainWindow.__init__(self)#主界面对象初始化
                self.setupUi(self)  #配置主界面对象

    else:
        class CoperQt(QMainWindow,routerui.Ui_MainWindow):#创建一个Qt对象
        #这里的第一个变量是你该窗口的类型，第二个是该窗口对象。
        #这里是主窗口类型。所以设置成当QtWidgets.QMainWindow。
        #你的窗口是一个会话框时你需要设置成:QtWidgets.QDialog
            def __init__(self):
                QMainWindow.__init__(self)  # 创建主界面对象
                routerui.Ui_MainWindow.__init__(self)#主界面对象初始化
                self.setupUi(self)  #配置主界面对象

    app = QApplication(sys.argv)
    window = CoperQt()#创建QT对象
    # window.setTrafficText('Hello World')
    window.show()#QT对象显示
    sys.exit(app.exec_())

