# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/main_window.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(736, 464)
        MainWindow.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        MainWindow.setWindowTitle("easyp2p")
        MainWindow.setDocumentMode(False)
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralWidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.group_box_platform_top = QtWidgets.QGroupBox(self.centralWidget)
        self.group_box_platform_top.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.group_box_platform_top.setAlignment(QtCore.Qt.AlignCenter)
        self.group_box_platform_top.setObjectName("group_box_platform_top")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.group_box_platform_top)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.group_box_platforms = QtWidgets.QGroupBox(self.group_box_platform_top)
        self.group_box_platforms.setTitle("")
        self.group_box_platforms.setObjectName("group_box_platforms")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.group_box_platforms)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.check_box_bondora = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_bondora.setText("Bondora")
        self.check_box_bondora.setShortcut("")
        self.check_box_bondora.setObjectName("check_box_bondora")
        self.gridLayout_2.addWidget(self.check_box_bondora, 0, 0, 1, 1)
        self.check_box_mintos = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_mintos.setText("Mintos")
        self.check_box_mintos.setShortcut("")
        self.check_box_mintos.setObjectName("check_box_mintos")
        self.gridLayout_2.addWidget(self.check_box_mintos, 0, 1, 1, 1)
        self.check_box_dofinance = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_dofinance.setText("DoFinance")
        self.check_box_dofinance.setShortcut("")
        self.check_box_dofinance.setObjectName("check_box_dofinance")
        self.gridLayout_2.addWidget(self.check_box_dofinance, 2, 0, 1, 1)
        self.check_box_peerberry = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_peerberry.setText("PeerBerry")
        self.check_box_peerberry.setShortcut("")
        self.check_box_peerberry.setObjectName("check_box_peerberry")
        self.gridLayout_2.addWidget(self.check_box_peerberry, 2, 1, 1, 1)
        self.check_box_estateguru = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_estateguru.setText("Estateguru")
        self.check_box_estateguru.setShortcut("")
        self.check_box_estateguru.setObjectName("check_box_estateguru")
        self.gridLayout_2.addWidget(self.check_box_estateguru, 4, 0, 1, 1)
        self.check_box_robocash = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_robocash.setText("Robocash")
        self.check_box_robocash.setShortcut("")
        self.check_box_robocash.setObjectName("check_box_robocash")
        self.gridLayout_2.addWidget(self.check_box_robocash, 4, 1, 1, 1)
        self.check_box_grupeer = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_grupeer.setText("Grupeer")
        self.check_box_grupeer.setShortcut("")
        self.check_box_grupeer.setObjectName("check_box_grupeer")
        self.gridLayout_2.addWidget(self.check_box_grupeer, 6, 0, 1, 1)
        self.check_box_swaper = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_swaper.setText("Swaper")
        self.check_box_swaper.setShortcut("")
        self.check_box_swaper.setObjectName("check_box_swaper")
        self.gridLayout_2.addWidget(self.check_box_swaper, 6, 1, 1, 1)
        self.check_box_iuvo = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_iuvo.setText("Iuvo")
        self.check_box_iuvo.setShortcut("")
        self.check_box_iuvo.setObjectName("check_box_iuvo")
        self.gridLayout_2.addWidget(self.check_box_iuvo, 7, 0, 1, 1)
        self.check_box_twino = QtWidgets.QCheckBox(self.group_box_platforms)
        self.check_box_twino.setText("Twino")
        self.check_box_twino.setShortcut("")
        self.check_box_twino.setObjectName("check_box_twino")
        self.gridLayout_2.addWidget(self.check_box_twino, 7, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout_2, 0, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.group_box_platforms)
        self.check_box_select_all = QtWidgets.QCheckBox(self.group_box_platform_top)
        self.check_box_select_all.setObjectName("check_box_select_all")
        self.verticalLayout_3.addWidget(self.check_box_select_all)
        self.gridLayout_4.addLayout(self.verticalLayout_3, 0, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.group_box_platform_top)
        self.horizontalLayout_date_range = QtWidgets.QHBoxLayout()
        self.horizontalLayout_date_range.setObjectName("horizontalLayout_date_range")
        self.groupBox_start_date = QtWidgets.QGroupBox(self.centralWidget)
        self.groupBox_start_date.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.groupBox_start_date.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox_start_date.setObjectName("groupBox_start_date")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_start_date)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.combo_box_start_month = QtWidgets.QComboBox(self.groupBox_start_date)
        self.combo_box_start_month.setObjectName("combo_box_start_month")
        self.horizontalLayout_3.addWidget(self.combo_box_start_month)
        self.combo_box_start_year = QtWidgets.QComboBox(self.groupBox_start_date)
        self.combo_box_start_year.setObjectName("combo_box_start_year")
        self.horizontalLayout_3.addWidget(self.combo_box_start_year)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_date_range.addWidget(self.groupBox_start_date)
        self.groupBox_end_date = QtWidgets.QGroupBox(self.centralWidget)
        self.groupBox_end_date.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox_end_date.setObjectName("groupBox_end_date")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.groupBox_end_date)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.combo_box_end_month = QtWidgets.QComboBox(self.groupBox_end_date)
        self.combo_box_end_month.setObjectName("combo_box_end_month")
        self.horizontalLayout_4.addWidget(self.combo_box_end_month)
        self.combo_box_end_year = QtWidgets.QComboBox(self.groupBox_end_date)
        self.combo_box_end_year.setObjectName("combo_box_end_year")
        self.horizontalLayout_4.addWidget(self.combo_box_end_year)
        self.horizontalLayout_5.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_date_range.addWidget(self.groupBox_end_date)
        self.verticalLayout_2.addLayout(self.horizontalLayout_date_range)
        self.groupBox_5 = QtWidgets.QGroupBox(self.centralWidget)
        self.groupBox_5.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.groupBox_5.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox_5.setObjectName("groupBox_5")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox_5)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.line_edit_output_file = QtWidgets.QLineEdit(self.groupBox_5)
        self.line_edit_output_file.setReadOnly(True)
        self.line_edit_output_file.setObjectName("line_edit_output_file")
        self.horizontalLayout_6.addWidget(self.line_edit_output_file)
        self.push_button_file_chooser = QtWidgets.QPushButton(self.groupBox_5)
        self.push_button_file_chooser.setObjectName("push_button_file_chooser")
        self.horizontalLayout_6.addWidget(self.push_button_file_chooser)
        self.verticalLayout_5.addLayout(self.horizontalLayout_6)
        self.verticalLayout_2.addWidget(self.groupBox_5)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.push_button_start = QtWidgets.QPushButton(self.centralWidget)
        self.push_button_start.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.push_button_start.setObjectName("push_button_start")
        self.horizontalLayout.addWidget(self.push_button_start)
        self.tool_button_settings = QtWidgets.QToolButton(self.centralWidget)
        self.tool_button_settings.setText("...")
        self.tool_button_settings.setObjectName("tool_button_settings")
        self.horizontalLayout.addWidget(self.tool_button_settings)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 736, 30))
        self.menuBar.setObjectName("menuBar")
        self.menuLanguage = QtWidgets.QMenu(self.menuBar)
        self.menuLanguage.setObjectName("menuLanguage")
        MainWindow.setMenuBar(self.menuBar)
        self.actionEnglish = QtWidgets.QAction(MainWindow)
        self.actionEnglish.setCheckable(True)
        self.actionEnglish.setChecked(True)
        self.actionEnglish.setObjectName("actionEnglish")
        self.actionGerman = QtWidgets.QAction(MainWindow)
        self.actionGerman.setCheckable(True)
        self.actionGerman.setEnabled(True)
        self.actionGerman.setObjectName("actionGerman")
        self.menuLanguage.addAction(self.actionEnglish)
        self.menuLanguage.addAction(self.actionGerman)
        self.menuBar.addAction(self.menuLanguage.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        self.group_box_platform_top.setTitle(_translate("MainWindow", "For which P2P platforms should the results be loaded?"))
        self.check_box_select_all.setText(_translate("MainWindow", "Select/deselect all"))
        self.groupBox_start_date.setTitle(_translate("MainWindow", "Start date"))
        self.groupBox_end_date.setTitle(_translate("MainWindow", "End date"))
        self.groupBox_5.setTitle(_translate("MainWindow", "Where should the results be saved?"))
        self.push_button_file_chooser.setText(_translate("MainWindow", "Choose File"))
        self.push_button_start.setText(_translate("MainWindow", "Start evaluation"))
        self.menuLanguage.setTitle(_translate("MainWindow", "&Language"))
        self.actionEnglish.setText(_translate("MainWindow", "English"))
        self.actionGerman.setText(_translate("MainWindow", "German"))


