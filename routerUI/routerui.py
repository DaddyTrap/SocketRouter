# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '.\mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
sys.path.append("..")
import route_node
import json
import threading
class Ui_MainWindow(object):
    PACKET = {
        "packet_type": route_node.BaseRouteNode.PACKET_DATA,
        "data_type": route_node.BaseRouteNode.DATA_TXT,
        "data": b'Hey guy!'
    }

    change_ui_lock = threading.Lock()
    change_ui_signal_change = QtCore.pyqtSignal()
    change_ui_signal_handler = QtCore.pyqtSignal()
    change_ui_thread_change = None
    change_ui_thread_handler = None

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(482, 635)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Data = QtWidgets.QTextEdit(self.centralwidget)
        self.Data.setGeometry(QtCore.QRect(20, 190, 171, 31))
        self.Data.setObjectName("Data")
        self.TargetAddress = QtWidgets.QTextEdit(self.centralwidget)
        self.TargetAddress.setGeometry(QtCore.QRect(280, 190, 171, 31))
        self.TargetAddress.setObjectName("TargetAddress")
        self.SendTo = QtWidgets.QLabel(self.centralwidget)
        self.SendTo.setGeometry(QtCore.QRect(210, 200, 54, 20))
        self.SendTo.setObjectName("SendTo")
        self.Send = QtWidgets.QPushButton(self.centralwidget)
        self.Send.setGeometry(QtCore.QRect(20, 230, 75, 23))
        self.Send.setObjectName("Send")
        self.CostTable = QtWidgets.QTextBrowser(self.centralwidget)
        self.CostTable.setGeometry(QtCore.QRect(20, 300, 171, 121))
        self.CostTable.setObjectName("CostTable")
        self.ForwardTable = QtWidgets.QTextBrowser(self.centralwidget)
        self.ForwardTable.setGeometry(QtCore.QRect(280, 300, 181, 121))
        self.ForwardTable.setObjectName("ForwardTable")
        self.CostTableTitle = QtWidgets.QLabel(self.centralwidget)
        self.CostTableTitle.setGeometry(QtCore.QRect(70, 280, 81, 16))
        self.CostTableTitle.setObjectName("CostTableTitle")
        self.ForwardTableTitle = QtWidgets.QLabel(self.centralwidget)
        self.ForwardTableTitle.setGeometry(QtCore.QRect(330, 280, 101, 16))
        self.ForwardTableTitle.setObjectName("ForwardTableTitle")
        self.LsAlgoBtn = QtWidgets.QPushButton(self.centralwidget)
        self.LsAlgoBtn.setGeometry(QtCore.QRect(10, 560, 101, 21))
        self.LsAlgoBtn.setObjectName("LsAlgoBtn")
        self.DvAlgoBtn = QtWidgets.QPushButton(self.centralwidget)
        self.DvAlgoBtn.setGeometry(QtCore.QRect(130, 560, 101, 21))
        self.DvAlgoBtn.setObjectName("DvAlgoBtn")
        self.NodeIDTitle = QtWidgets.QLabel(self.centralwidget)
        self.NodeIDTitle.setGeometry(QtCore.QRect(20, 10, 41, 20))
        self.NodeIDTitle.setObjectName("NodeIDTitle")
        self.NodeId = QtWidgets.QTextBrowser(self.centralwidget)
        self.NodeId.setGeometry(QtCore.QRect(60, 10, 71, 31))
        self.NodeId.setObjectName("NodeId")
        self.TrafficLog = QtWidgets.QTextBrowser(self.centralwidget)
        self.TrafficLog.setGeometry(QtCore.QRect(20, 90, 451, 81))
        self.TrafficLog.setObjectName("TrafficLog")
        self.TrafficlogTable = QtWidgets.QLabel(self.centralwidget)
        self.TrafficlogTable.setGeometry(QtCore.QRect(20, 60, 91, 20))
        self.TrafficlogTable.setObjectName("TrafficlogTable")
        self.CentralNodeIdTitle = QtWidgets.QLabel(self.centralwidget)
        self.CentralNodeIdTitle.setGeometry(QtCore.QRect(320, 10, 71, 20))
        self.CentralNodeIdTitle.setObjectName("CentralNodeIdTitle")
        self.CentralNodeId = QtWidgets.QTextBrowser(self.centralwidget)
        self.CentralNodeId.setGeometry(QtCore.QRect(400, 10, 71, 31))
        self.CentralNodeId.setObjectName("CentralNodeId")
        self.routeinit = QtWidgets.QTextEdit(self.centralwidget)
        self.routeinit.setGeometry(QtCore.QRect(10, 440, 461, 111))
        self.routeinit.setObjectName("routeinit")
        self.StopNode = QtWidgets.QPushButton(self.centralwidget)
        self.StopNode.setGeometry(QtCore.QRect(260, 560, 81, 23))
        self.StopNode.setObjectName("StopNode")
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
        self.DvAlgoBtn.clicked.connect(self.UseDv)
        self.LsAlgoBtn.clicked.connect(self.UseLs)
        self.StopNode.clicked.connect(self.NodeStop)
        self.Send.clicked.connect(self.SendData)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.Send.setEnabled(False)
        self.node = None
        self.StopNode.setEnabled(False)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.SendTo.setText(_translate("MainWindow", "Send To"))
        self.Send.setText(_translate("MainWindow", "Send"))
        self.CostTableTitle.setText(_translate("MainWindow", "Cost Table"))
        self.ForwardTableTitle.setText(_translate("MainWindow", "Forward Table"))
        self.LsAlgoBtn.setText(_translate("MainWindow", "Create LSNode"))
        self.DvAlgoBtn.setText(_translate("MainWindow", "Create DVNode"))
        self.NodeIDTitle.setText(_translate("MainWindow", "NodeID"))
        self.TrafficlogTable.setText(_translate("MainWindow", "log"))
        self.CentralNodeIdTitle.setText(_translate("MainWindow", "Central NodeID"))
        self.StopNode.setText(_translate("MainWindow", "Stop Node"))
        self.menuRouter.setTitle(_translate("MainWindow", "Router"))

    class WrapperThread(QtCore.QThread):
        def __init__(self, sig, func, obj):
            QtCore.QThread.__init__(self)
            self.sig = sig
            self.func = func
            self.obj = obj
            self.finished.connect(self.onfinish)

        def run(self):
            self.sig.emit()
            # print("emitted")
            self.exit()
            # print("bye")
            # self.sig.disconnect(self.func)
            # self.obj.change_ui_lock.release()

        def onfinish(self):
            self.wait()

        def __del__(self):
            self.wait()

    def change(self,node_instance):
        # print("in change")
        cost_table = self.CostTable
        forward_table = self.ForwardTable
        @QtCore.pyqtSlot()
        def _change():
            # print("in _change")
            cText = ""
            fText = ""
            for k,v in node_instance.cost_table.items():
                cText += 'cost %d to reach node %d\n' % (v,k)
            cost_table.setText(cText)
            for k,v in node_instance.forward_table.items():
                fText += 'reach node %d via node %d\n' % (v,k)
            forward_table.setText(fText)
        # self.change_ui_lock.acquire()
        self.change_ui_thread_change = self.WrapperThread(self.change_ui_signal_change, _change, self)
        self.change_ui_signal_change.connect(_change)
        self.change_ui_thread_change.start()

    def handler(self,obj):
        # print("in handler")
        # traffic_log = self.TrafficLog
        # @QtCore.pyqtSlot()
        # def _handler():
        #     print("in _handler")
        #     traffic_log.setText('rev packet ' + str(obj))
        # # self.change_ui_lock.acquire()
        # self.change_ui_thread_handler = self.WrapperThread(self.change_ui_signal_handler, _handler, self)
        # self.change_ui_signal_handler.connect(_handler)
        # self.change_ui_thread_handler.start()
        self.TrafficLog.append('recv from node %d: %s' % (obj['src_id'],obj['data'].decode()))

    def SendData(self):
        data = self.Data.toPlainText()
        target = self.TargetAddress.toPlainText()
        self.PACKET["data"] = data.encode()
        self.node.send(self.PACKET, int(target))
        self.TrafficLog.append('send to node %s ： %s' % (target,data))

    def UseLs(self):
        if self.node != None:
            del self.node
        try:
            initinfo = json.loads(self.routeinit.toPlainText())
        except:
            self.TrafficLog.append("Please input info with json format\n")
            return
        self.UIChangeOnStart()
        self.node = route_node.LSRouteNode(initinfo, obj_handler=self.handler, data_change_handler=self.change)
        self.NodeId.setText(str(self.node.node_id))
        self.node.start()


    def UseDv(self):
        if self.node != None:
            del self.node
        try:
            initinfo = json.loads(self.routeinit.toPlainText())
        except:
            self.TrafficLog.append("Please input info with json format\n")
            return
        self.UIChangeOnStart()
        self.node =  route_node.DVRouteNode(initinfo, obj_handler=self.handler, data_change_handler=self.change)
        self.NodeId.setText(str(self.node.node_id))
        self.node.start()

    def NodeStop(self):
        self.UIChangeOnStop()
        self.node.stop()
        self.node.recv_sock.close()
        self.node = None

    def UIChangeOnStart(self):
        self.DvAlgoBtn.setEnabled(False)
        self.LsAlgoBtn.setEnabled(False)
        self.StopNode.setEnabled(True)
        self.routeinit.setReadOnly(True)
        self.Send.setEnabled(True)

    def UIChangeOnStop(self):
        self.routeinit.setReadOnly(False)
        self.StopNode.setEnabled(False)
        self.DvAlgoBtn.setEnabled(True)
        self.LsAlgoBtn.setEnabled(True)
        self.Send.setEnabled(False)
