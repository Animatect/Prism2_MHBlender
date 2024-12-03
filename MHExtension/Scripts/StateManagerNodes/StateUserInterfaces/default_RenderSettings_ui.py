# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'default_RenderSettings.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from qtpy.QtCore import *  # type: ignore
from qtpy.QtGui import *  # type: ignore
from qtpy.QtWidgets import *  # type: ignore

class Ui_wg_RenderSettings(object):
    def setupUi(self, wg_RenderSettings):
        if not wg_RenderSettings.objectName():
            wg_RenderSettings.setObjectName(u"wg_RenderSettings")
        wg_RenderSettings.resize(340, 449)
        self.verticalLayout = QVBoxLayout(wg_RenderSettings)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.f_name = QWidget(wg_RenderSettings)
        self.f_name.setObjectName(u"f_name")
        self.horizontalLayout_4 = QHBoxLayout(self.f_name)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(9, 0, 18, 0)
        self.l_name = QLabel(self.f_name)
        self.l_name.setObjectName(u"l_name")

        self.horizontalLayout_4.addWidget(self.l_name)

        self.e_name = QLineEdit(self.f_name)
        self.e_name.setObjectName(u"e_name")

        self.horizontalLayout_4.addWidget(self.e_name)

        self.l_class = QLabel(self.f_name)
        self.l_class.setObjectName(u"l_class")
        font = QFont()
        font.setBold(True)
        self.l_class.setFont(font)

        self.horizontalLayout_4.addWidget(self.l_class)


        self.verticalLayout.addWidget(self.f_name)

        self.gb_general = QGroupBox(wg_RenderSettings)
        self.gb_general.setObjectName(u"gb_general")
        self.verticalLayout_2 = QVBoxLayout(self.gb_general)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.w_load_3 = QWidget(self.gb_general)
        self.w_load_3.setObjectName(u"w_load_3")
        self.horizontalLayout_12 = QHBoxLayout(self.w_load_3)
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(9, 0, 9, 0)
        self.chb_editSettings = QCheckBox(self.w_load_3)
        self.chb_editSettings.setObjectName(u"chb_editSettings")

        self.horizontalLayout_12.addWidget(self.chb_editSettings)


        self.verticalLayout_2.addWidget(self.w_load_3)

        self.w_presetOption = QWidget(self.gb_general)
        self.w_presetOption.setObjectName(u"w_presetOption")
        self.horizontalLayout_13 = QHBoxLayout(self.w_presetOption)
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(9, 0, 9, 0)
        self.l_presetOption = QLabel(self.w_presetOption)
        self.l_presetOption.setObjectName(u"l_presetOption")

        self.horizontalLayout_13.addWidget(self.l_presetOption)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer)

        self.cb_presetOption = QComboBox(self.w_presetOption)
        self.cb_presetOption.setObjectName(u"cb_presetOption")

        self.horizontalLayout_13.addWidget(self.cb_presetOption)


        self.verticalLayout_2.addWidget(self.w_presetOption)

        self.w_loadCurrent = QWidget(self.gb_general)
        self.w_loadCurrent.setObjectName(u"w_loadCurrent")
        self.horizontalLayout_11 = QHBoxLayout(self.w_loadCurrent)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(9, 0, 9, 0)
        self.b_loadCurrent = QPushButton(self.w_loadCurrent)
        self.b_loadCurrent.setObjectName(u"b_loadCurrent")

        self.horizontalLayout_11.addWidget(self.b_loadCurrent)

        self.b_loadPreset = QPushButton(self.w_loadCurrent)
        self.b_loadPreset.setObjectName(u"b_loadPreset")

        self.horizontalLayout_11.addWidget(self.b_loadPreset)


        self.verticalLayout_2.addWidget(self.w_loadCurrent)

        self.w_addSetting = QWidget(self.gb_general)
        self.w_addSetting.setObjectName(u"w_addSetting")
        self.horizontalLayout = QHBoxLayout(self.w_addSetting)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(9, 0, 9, 0)
        self.cb_addSetting = QComboBox(self.w_addSetting)
        self.cb_addSetting.setObjectName(u"cb_addSetting")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cb_addSetting.sizePolicy().hasHeightForWidth())
        self.cb_addSetting.setSizePolicy(sizePolicy)
        self.cb_addSetting.setEditable(True)
        self.cb_addSetting.setMaxVisibleItems(30)

        self.horizontalLayout.addWidget(self.cb_addSetting)


        self.verticalLayout_2.addWidget(self.w_addSetting)

        self.gb_settings = QGroupBox(self.gb_general)
        self.gb_settings.setObjectName(u"gb_settings")
        self.verticalLayout_3 = QVBoxLayout(self.gb_settings)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.te_settings = QTextEdit(self.gb_settings)
        self.te_settings.setObjectName(u"te_settings")
        self.te_settings.setLineWrapMode(QTextEdit.NoWrap)

        self.verticalLayout_3.addWidget(self.te_settings)


        self.verticalLayout_2.addWidget(self.gb_settings)

        self.w_save = QWidget(self.gb_general)
        self.w_save.setObjectName(u"w_save")
        self.horizontalLayout_2 = QHBoxLayout(self.w_save)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(9, 0, 9, 0)
        self.b_resetSettings = QPushButton(self.w_save)
        self.b_resetSettings.setObjectName(u"b_resetSettings")

        self.horizontalLayout_2.addWidget(self.b_resetSettings)

        self.b_applySettings = QPushButton(self.w_save)
        self.b_applySettings.setObjectName(u"b_applySettings")
        self.b_applySettings.setEnabled(True)
        self.b_applySettings.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_2.addWidget(self.b_applySettings)


        self.verticalLayout_2.addWidget(self.w_save)

        self.w_load = QWidget(self.gb_general)
        self.w_load.setObjectName(u"w_load")
        self.horizontalLayout_10 = QHBoxLayout(self.w_load)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(9, 0, 9, 0)
        self.b_savePreset = QPushButton(self.w_load)
        self.b_savePreset.setObjectName(u"b_savePreset")
        self.b_savePreset.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_10.addWidget(self.b_savePreset)


        self.verticalLayout_2.addWidget(self.w_load)


        self.verticalLayout.addWidget(self.gb_general)


        self.retranslateUi(wg_RenderSettings)

        QMetaObject.connectSlotsByName(wg_RenderSettings)
    # setupUi

    def retranslateUi(self, wg_RenderSettings):
        wg_RenderSettings.setWindowTitle(QCoreApplication.translate("wg_RenderSettings", u"Render Settings", None))
        self.l_name.setText(QCoreApplication.translate("wg_RenderSettings", u"Name:", None))
        self.l_class.setText(QCoreApplication.translate("wg_RenderSettings", u"Render Settings", None))
        self.gb_general.setTitle(QCoreApplication.translate("wg_RenderSettings", u"General", None))
        self.chb_editSettings.setText(QCoreApplication.translate("wg_RenderSettings", u"Edit settings", None))
        self.l_presetOption.setText(QCoreApplication.translate("wg_RenderSettings", u"Preset:", None))
        self.b_loadCurrent.setText(QCoreApplication.translate("wg_RenderSettings", u"Get current settings", None))
        self.b_loadPreset.setText(QCoreApplication.translate("wg_RenderSettings", u"Load preset...", None))
        self.gb_settings.setTitle(QCoreApplication.translate("wg_RenderSettings", u"Settings", None))
        self.b_resetSettings.setText(QCoreApplication.translate("wg_RenderSettings", u"Apply default settings", None))
        self.b_applySettings.setText(QCoreApplication.translate("wg_RenderSettings", u"Apply preset", None))
        self.b_savePreset.setText(QCoreApplication.translate("wg_RenderSettings", u"Save new preset...", None))
    # retranslateUi

