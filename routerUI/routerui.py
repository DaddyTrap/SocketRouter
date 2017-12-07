# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(472, 440)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.SendData = QtWidgets.QTextEdit(self.centralwidget)
        self.SendData.setGeometry(QtCore.QRect(20, 10, 171, 31))
        self.SendData.setObjectName("SendData")
        self.TargetAddress = QtWidgets.QTextEdit(self.centralwidget)
        self.TargetAddress.setGeometry(QtCore.QRect(280, 10, 171, 31))
        self.TargetAddress.setObjectName("TargetAddress")
        self.SendTo = QtWidgets.QLabel(self.centralwidget)
        self.SendTo.setGeometry(QtCore.QRect(210, 20, 54, 20))
        self.SendTo.setObjectName("SendTo")
        self.Send = QtWidgets.QPushButton(self.centralwidget)
        self.Send.setGeometry(QtCore.QRect(20, 50, 75, 23))
        self.Send.setObjectName("Send")
        self.CostTable = QtWidgets.QTextBrowser(self.centralwidget)
        self.CostTable.setGeometry(QtCore.QRect(20, 110, 171, 121))
        self.CostTable.setObjectName("CostTable")
        self.ForwardTable = QtWidgets.QTextBrowser(self.centralwidget)
        self.ForwardTable.setGeometry(QtCore.QRect(280, 110, 181, 121))
        self.ForwardTable.setObjectName("ForwardTable")
        self.CostTableTitle = QtWidgets.QLabel(self.centralwidget)
        self.CostTableTitle.setGeometry(QtCore.QRect(70, 90, 81, 16))
        self.CostTableTitle.setObjectName("CostTableTitle")
        self.ForwardTableTitle = QtWidgets.QLabel(self.centralwidget)
        self.ForwardTableTitle.setGeometry(QtCore.QRect(330, 90, 101, 16))
        self.ForwardTableTitle.setObjectName("ForwardTableTitle")
        self.LsAlgoBtn = QtWidgets.QPushButton(self.centralwidget)
        self.LsAlgoBtn.setGeometry(QtCore.QRect(20, 240, 101, 21))
        self.LsAlgoBtn.setObjectName("LsAlgoBtn")
        self.DvAlgoBtn = QtWidgets.QPushButton(self.centralwidget)
        self.DvAlgoBtn.setGeometry(QtCore.QRect(130, 240, 101, 21))
        self.DvAlgoBtn.setObjectName("DvAlgoBtn")
        self.NodeIDTitle = QtWidgets.QLabel(self.centralwidget)
        self.NodeIDTitle.setGeometry(QtCore.QRect(380, 290, 41, 20))
        self.NodeIDTitle.setObjectName("NodeIDTitle")
        self.NodeId = QtWidgets.QTextBrowser(self.centralwidget)
        self.NodeId.setGeometry(QtCore.QRect(380, 310, 71, 31))
        self.NodeId.setObjectName("NodeId")
        self.TrafficLog = QtWidgets.QTextBrowser(self.centralwidget)
        self.TrafficLog.setGeometry(QtCore.QRect(10, 310, 281, 81))
        self.TrafficLog.setObjectName("TrafficLog")
        self.TrafficlogTable = QtWidgets.QLabel(self.centralwidget)
        self.TrafficlogTable.setGeometry(QtCore.QRect(10, 290, 91, 20))
        self.TrafficlogTable.setObjectName("TrafficlogTable")
        self.CentralNodeIdTitle = QtWidgets.QLabel(self.centralwidget)
        self.CentralNodeIdTitle.setGeometry(QtCore.QRect(380, 340, 91, 20))
        self.CentralNodeIdTitle.setObjectName("CentralNodeIdTitle")
        self.CentralNodeId = QtWidgets.QTextBrowser(self.centralwidget)
        self.CentralNodeId.setGeometry(QtCore.QRect(380, 360, 71, 31))
        self.CentralNodeId.setObjectName("CentralNodeId")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 472, 23))
        self.menubar.setObjectName("menubar")
        self.menuRouter = QtWidgets.QMenu(self.menubar)
        self.menuRouter.setObjectName("menuRouter")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menuRouter.menuAction())

        self.retranslateUi(MainWindow)
        self.Send.clicked.connect(MainWindow.SendData)
        self.LsAlgoBtn.clicked.connect(MainWindow.UseLs)
        self.DvAlgoBtn.clicked.connect(MainWindow.UseDv)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.SendTo.setText(_translate("MainWindow", "Send To"))
        self.Send.setText(_translate("MainWindow", "Send"))
        self.CostTableTitle.setText(_translate("MainWindow", "Cost Table"))
        self.ForwardTableTitle.setText(_translate("MainWindow", "Forward Table"))
        self.LsAlgoBtn.setText(_translate("MainWindow", "Use Ls Algo"))
        self.DvAlgoBtn.setText(_translate("MainWindow", "Use Dv Algo"))
        self.NodeIDTitle.setText(_translate("MainWindow", "NodeID"))
        self.TrafficlogTable.setText(_translate("MainWindow", "Traffic log"))
        self.CentralNodeIdTitle.setText(_translate("MainWindow", "Central NodeID"))
        self.menuRouter.setTitle(_translate("MainWindow", "Router"))


    def SendData(self, SendFunc):
        data = self.SendData.toPlainText()
        target = self.TargetAddress.toPlainText()

    def UseLs(self):
        pass

    def UseDv(self):
        pass

    def UpdateTrafficText(self,text):
        self.TrafficLog.append(text)

    def printCostTable(self, text):
        self.CostTable.setText(text)

    def printForwardTable(self, text):
        self.ForwardTable.setText(text)
    
    def setNodeId(self,text):
        self.NodeId.setText(text)

    def setCentralNodeId(self, text):
        self.CentralNodeId.setText(text)