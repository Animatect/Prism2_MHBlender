# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2023 Richard Frangenberg
# Copyright (C) 2023 Prism Software GmbH
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.


import os
import sys
import time
import platform

from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *

from PrismUtils.Decorators import err_catcher


class MHrendLayerClass(object):
    className = "MHrendLayer"
    listType = "Export"
    stateCategories = {"Render": [{"label": className, "stateType": className}]}

    @err_catcher(name=__name__)
    def setup(self, state, core, stateManager, node=None, stateData=None):
        self.state = state
        self.core = core
        self.stateManager = stateManager
        self.canSetVersion = True
        self.customContext = None
        self.allowCustomContext = False
        self.cb_context.addItems(["From scenefile", "Custom"])
        
        self.pluginMHfunctions = self.core.getPlugin("MHBlenderExtension").functions
        self.dynamic_checkboxes = []
        self.layername = ""
        
        self.curCam = None
        self.renderingStarted = False
        self.cleanOutputdir = True

        self.e_name.setText(state.text(0) + " - {identifier}")

        self.rangeTypes = [
            "Scene",
            "Shot",
            "Single Frame",
            "Custom",
            "Expression",
        ]
        self.cb_rangeType.addItems(self.rangeTypes)
        for idx, rtype in enumerate(self.rangeTypes):
            self.cb_rangeType.setItemData(
                idx, self.stateManager.getFrameRangeTypeToolTip(rtype), Qt.ToolTipRole
            )
        self.w_frameExpression.setToolTip(
            self.stateManager.getFrameRangeTypeToolTip("ExpressionField")
        )

        self.renderPresets = (
            self.stateManager.stateTypes["RenderSettings"].getPresets(self.core)
            if "RenderSettings" in self.stateManager.stateTypes
            else {}
        )
        if self.renderPresets:
            self.cb_renderPreset.addItems(self.renderPresets.keys())
        else:
            self.w_renderPreset.setVisible(False)
        
        self.w_context.setVisible(False)
        # self.f_taskname.setVisible(False)
        self.b_changeTask.setVisible(False)
        self.label_2.setVisible(False)
        self.l_name.setVisible(False)
        self.e_name.setVisible(False)
        self.f_range.setVisible(False)
        self.w_frameRangeValues.setVisible(False)
        self.f_cam.setVisible(False)
        self.f_resolution.setVisible(False)
        self.w_format.setVisible(False)
        self.gb_submit.setChecked(False)
        self.gb_submit.setVisible(False)
        self.f_renderLayer.setVisible(True)
        self.chb_dontUpdateV.setChecked(False)

        getattr(self.core.appPlugin, "sm_render_startup", lambda x: None)(self)

        masterItems = ["Set as master", "Add to master", "Don't update master"]
        self.cb_master.addItems(masterItems)
        self.product_paths = self.core.paths.getRenderProductBasePaths()
        self.cb_outPath.addItems(list(self.product_paths.keys()))
        if len(self.product_paths) < 2:
            self.w_outPath.setVisible(False)

        self.mediaType = "3drenders"
        self.tasknameRequired = True
        self.outputFormats = [
            ".exr",
            ".png",
            ".jpg",
        ]
        
        self.cb_format.addItems(self.outputFormats)

        layers = self.pluginMHfunctions.getRenderLayers()
        self.cb_renderLayer.addItems(layers)
        self.layername = self.cb_renderLayer.currentText()

        self.resolutionPresets = self.core.projects.getResolutionPresets()
        if "Get from rendersettings" not in self.resolutionPresets:
            self.resolutionPresets.append("Get from rendersettings")

        self.e_osSlaves.setText("All")

        self.connectEvents()

        self.oldPalette = self.b_changeTask.palette()
        self.warnPalette = QPalette()
        self.warnPalette.setColor(QPalette.Button, QColor(200, 0, 0))
        self.warnPalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))

        self.setTaskWarn(True)
        self.nameChanged(state.text(0))

        self.cb_manager.addItems([p.pluginName for p in self.core.plugins.getRenderfarmPlugins()])
        self.core.callback("onStateStartup", self)
        if self.cb_manager.count() == 0:
            self.gb_submit.setVisible(False)

        self.managerChanged(True)

        if stateData is not None:
            self.loadData(stateData)
        else:
            self.initializeContextBasedSettings()
        
        # Connect the toggle event for the whole thing.
        self.stateManager.tw_export.itemChanged.connect(self.sm_toggleLayerNodes)
        
        elements = list(self.pluginMHfunctions.layerProperties.keys())
        self.addPropertyWidget(elements)

        self.updateLayerProperties()

        # Check if the layer is selected and change it.
        self.on_RenderLayerCb_setup()

        # Cosmetic tweak to borders.
        self.handleExtraCSS()

    @err_catcher(name=__name__)
    def handleExtraCSS(self):
        ## BORDERS ##
        # Remove borders
        self.setStyleSheet("""
            QGroupBox {
                border: none;
            }
        """)
        # Apply borders to specific Groupbox
        self.gb_layerProperties.setStyleSheet("border: 1px solid #3498db;")
        self.gb_layerpropertiestitle.setStyleSheet("border: none;")
        self.gb_properties.setStyleSheet("border: none;")
        self.gb_output.setStyleSheet("border: 1px solid #3498db;")
        self.gb_previous.setStyleSheet("border: none;")
        self.gb_donotupdateversion.setStyleSheet("border: none;")

        ## CHECKBOXES ##
        self.setStyleSheet("""
            QCheckBox::indicator:checked {
                background-color: #7dadfa;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3f3f3f;
            }
        """)
        


    @err_catcher(name=__name__)
    def loadData(self, data):
        if "contextType" in data:
            self.setContextType(data["contextType"])
        if "customContext" in data:
            self.customContext = data["customContext"]
        if "taskname" in data:
            self.setTaskname(data["taskname"])

        self.updateUi()

        if "stateName" in data:
            self.e_name.setText(data["stateName"])
        elif "statename" in data:
            self.e_name.setText(data["statename"] + " - {identifier}")
        if "renderpresetoverride" in data:
            res = eval(data["renderpresetoverride"])
            self.chb_renderPreset.setChecked(res)
        if "currentrenderpreset" in data:
            idx = self.cb_renderPreset.findText(data["currentrenderpreset"])
            if idx != -1:
                self.cb_renderPreset.setCurrentIndex(idx)
                self.stateManager.saveStatesToScene()
        if "rangeType" in data:
            idx = self.cb_rangeType.findText(data["rangeType"])
            if idx != -1:
                self.cb_rangeType.setCurrentIndex(idx)
                self.updateRange()
        if "startframe" in data:
            self.sp_rangeStart.setValue(int(data["startframe"]))
        if "endframe" in data:
            self.sp_rangeEnd.setValue(int(data["endframe"]))
        if "frameExpression" in data:
            self.le_frameExpression.setText(data["frameExpression"])
        if "currentcam" in data:
            camName = getattr(self.core.appPlugin, "getCamName", lambda x, y: "")(
                self, data["currentcam"]
            )
            idx = self.cb_cam.findText(camName)
            if idx != -1:
                self.curCam = self.camlist[idx]
                self.cb_cam.setCurrentIndex(idx)
                self.stateManager.saveStatesToScene()
        if "resoverride" in data:
            res = eval(data["resoverride"])
            self.chb_resOverride.setChecked(res[0])
            self.sp_resWidth.setValue(res[1])
            self.sp_resHeight.setValue(res[2])
        if "masterVersion" in data:
            idx = self.cb_master.findText(data["masterVersion"])
            if idx != -1:
                self.cb_master.setCurrentIndex(idx)
        if "curoutputpath" in data:
            idx = self.cb_outPath.findText(data["curoutputpath"])
            if idx != -1:
                self.cb_outPath.setCurrentIndex(idx)
        if "renderlayer" in data:
            idx = self.cb_renderLayer.findText(data["renderlayer"])
            if idx != -1:
                self.cb_renderLayer.setCurrentIndex(idx)
                self.stateManager.saveStatesToScene()
        if "outputFormat" in data:
            idx = self.cb_format.findText(data["outputFormat"])
            if idx != -1:
                self.cb_format.setCurrentIndex(idx)
        if "submitrender" in data:
            self.gb_submit.setChecked(eval(data["submitrender"]))
        if "rjmanager" in data:
            idx = self.cb_manager.findText(data["rjmanager"])
            if idx != -1:
                self.cb_manager.setCurrentIndex(idx)
            self.managerChanged(True)
        if "rjprio" in data:
            self.sp_rjPrio.setValue(int(data["rjprio"]))
        if "rjframespertask" in data:
            self.sp_rjFramesPerTask.setValue(int(data["rjframespertask"]))
        if "rjtimeout" in data:
            self.sp_rjTimeout.setValue(int(data["rjtimeout"]))
        if "rjsuspended" in data:
            self.chb_rjSuspended.setChecked(eval(data["rjsuspended"]))
        if "osdependencies" in data:
            self.chb_osDependencies.setChecked(eval(data["osdependencies"]))
        if "osupload" in data:
            self.chb_osUpload.setChecked(eval(data["osupload"]))
        if "ospassets" in data:
            self.chb_osPAssets.setChecked(eval(data["ospassets"]))
        if "osslaves" in data:
            self.e_osSlaves.setText(data["osslaves"])
        if "dlconcurrent" in data:
            self.sp_dlConcurrentTasks.setValue(int(data["dlconcurrent"]))
        if "dlgpupt" in data:
            self.sp_dlGPUpt.setValue(int(data["dlgpupt"]))
            self.gpuPtChanged()
        if "dlgpudevices" in data:
            self.le_dlGPUdevices.setText(data["dlgpudevices"])
            self.gpuDevicesChanged()
        if "enablepasses" in data:
            self.gb_passes.setChecked(eval(data["enablepasses"]))
        if "lastexportpath" in data:
            lePath = self.core.fixPath(data["lastexportpath"])
            self.l_pathLast.setText(lePath)
            self.l_pathLast.setToolTip(lePath)
        if "stateenabled" in data:
            if type(data["stateenabled"]) == int:
                self.state.setCheckState(
                    0, Qt.CheckState(data["stateenabled"]),
                )
        if "dontupdateversion" in data:
            self.chb_dontUpdateV.setChecked(eval(data["dontupdateversion"]))
            
        self.core.callback("onStateSettingsLoaded", self, data)

    @err_catcher(name=__name__)
    def connectEvents(self):
        self.e_name.textChanged.connect(self.nameChanged)
        self.e_name.editingFinished.connect(self.stateManager.saveStatesToScene)
        self.cb_context.activated.connect(self.onContextTypeChanged)
        self.b_context.clicked.connect(self.selectContextClicked)
        self.b_changeTask.clicked.connect(self.changeTask)
        self.chb_renderPreset.stateChanged.connect(self.presetOverrideChanged)
        self.cb_renderPreset.activated.connect(self.stateManager.saveStatesToScene)
        self.cb_rangeType.activated.connect(self.rangeTypeChanged)
        self.sp_rangeStart.editingFinished.connect(self.startChanged)
        self.sp_rangeEnd.editingFinished.connect(self.endChanged)
        self.le_frameExpression.textChanged.connect(self.frameExpressionChanged)
        self.le_frameExpression.editingFinished.connect(
            self.stateManager.saveStatesToScene
        )
        self.le_frameExpression.setMouseTracking(True)
        self.le_frameExpression.origMoveEvent = self.le_frameExpression.mouseMoveEvent
        self.le_frameExpression.mouseMoveEvent = self.exprMoveEvent
        self.le_frameExpression.leaveEvent = self.exprLeaveEvent
        self.le_frameExpression.focusOutEvent = self.exprFocusOutEvent
        self.cb_cam.activated.connect(self.setCam)
        self.chb_resOverride.stateChanged.connect(self.resOverrideChanged)
        self.sp_resWidth.editingFinished.connect(self.stateManager.saveStatesToScene)
        self.sp_resHeight.editingFinished.connect(self.stateManager.saveStatesToScene)
        self.b_resPresets.clicked.connect(self.showResPresets)
        self.cb_master.activated.connect(self.stateManager.saveStatesToScene)
        self.cb_outPath.activated.connect(self.stateManager.saveStatesToScene)
        self.cb_renderLayer.activated.connect(self.on_RenderLayerCb_changed)
        self.cb_format.activated.connect(self.stateManager.saveStatesToScene)
        self.gb_submit.toggled.connect(self.rjToggled)
        self.cb_manager.activated.connect(self.managerChanged)
        self.sp_rjPrio.editingFinished.connect(self.stateManager.saveStatesToScene)
        self.sp_rjFramesPerTask.editingFinished.connect(
            self.stateManager.saveStatesToScene
        )
        self.sp_rjTimeout.editingFinished.connect(self.stateManager.saveStatesToScene)
        self.chb_rjSuspended.stateChanged.connect(self.stateManager.saveStatesToScene)
        self.chb_osDependencies.stateChanged.connect(
            self.stateManager.saveStatesToScene
        )
        self.chb_osUpload.stateChanged.connect(self.stateManager.saveStatesToScene)
        self.chb_osPAssets.stateChanged.connect(self.stateManager.saveStatesToScene)
        self.e_osSlaves.editingFinished.connect(self.stateManager.saveStatesToScene)
        self.b_osSlaves.clicked.connect(self.openSlaves)
        self.sp_dlConcurrentTasks.editingFinished.connect(
            self.stateManager.saveStatesToScene
        )
        self.sp_dlGPUpt.editingFinished.connect(self.gpuPtChanged)
        self.le_dlGPUdevices.editingFinished.connect(self.gpuDevicesChanged)
        self.gb_passes.toggled.connect(self.stateManager.saveStatesToScene)
        self.b_addPasses.clicked.connect(self.showPasses)
        self.lw_passes.customContextMenuRequested.connect(self.rclickPasses)
        self.b_pathLast.clicked.connect(self.showLastPathMenu)
        self.lw_passes.itemDoubleClicked.connect(
            lambda x: self.pluginMHfunctions.sm_render_openPasses(self)
        )
        self.chb_dontUpdateV.stateChanged.connect(self.isDontUpdateVersionToggled)

    @err_catcher(name=__name__)
    def isDontUpdateVersionToggled(self, checked):
        if checked == Qt.Checked:
            checked = not checked == 0
        if not self.state.text(0).endswith(" - disabled"):
            sufix = " - VerNoUpdate"
            name = self.state.text(0)
            if checked:
                name += sufix
            else:
                if self.state.text(0).endswith(sufix):
                    name = name.replace(sufix, "")
            
            self.state.setText(0, name)
        self.stateManager.saveStatesToScene

    @err_catcher(name=__name__)
    def initializeContextBasedSettings(self):
        context = self.getCurrentContext()
        if context.get("type") == "asset":
            self.setRangeType("Single Frame")
        elif context.get("type") == "shot":
            self.setRangeType("Shot")
        elif self.stateManager.standalone:
            self.setRangeType("Custom")
        else:
            self.setRangeType("Scene")

        start, end = self.getFrameRange("Scene")
        if start is not None:
            self.sp_rangeStart.setValue(start)

        if end is not None:
            self.sp_rangeEnd.setValue(end)

        # if context.get("task"):
        #     self.setTaskname(context.get("task"))

        self.setTaskname(self.cb_renderLayer.currentText())

        self.updateUi()

    @err_catcher(name=__name__)
    def showLastPathMenu(self, state=None):
        path = self.l_pathLast.text()
        if path == "None":
            return

        menu = QMenu(self)

        act_open = QAction("Play", self)
        act_open.triggered.connect(lambda: self.core.media.playMediaInExternalPlayer(path))
        menu.addAction(act_open)

        act_open = QAction("Open in Media Browser", self)
        act_open.triggered.connect(lambda: self.openInMediaBrowser(path))
        menu.addAction(act_open)

        act_open = QAction("Open in explorer", self)
        print("open in explorer path: ",path)
        act_open.triggered.connect(lambda: self.core.openFolder(path))
        menu.addAction(act_open)

        act_copy = QAction("Copy", self)
        act_copy.triggered.connect(lambda: self.core.copyToClipboard(path, file=True))
        menu.addAction(act_copy)

        menu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def openInMediaBrowser(self, path):
        self.core.projectBrowser()
        self.core.pb.showTab("Media")
        data = self.core.paths.getRenderProductData(path)
        self.core.pb.mediaBrowser.showRender(entity=data, identifier=data.get("identifier"), version=data.get("version"))

    @err_catcher(name=__name__)
    def selectContextClicked(self, state=None):
        self.dlg_entity = self.stateManager.entityDlg(self)
        data = self.getCurrentContext()
        self.dlg_entity.w_entities.navigate(data)
        self.dlg_entity.entitySelected.connect(lambda x: self.setCustomContext(x))
        self.dlg_entity.show()

    @err_catcher(name=__name__)
    def setCustomContext(self, context):
        self.customContext = context
        self.refreshContext()
        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def onContextTypeChanged(self, state):
        self.refreshContext()
        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def rangeTypeChanged(self, state):
        self.updateUi()
        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def startChanged(self):
        if self.sp_rangeStart.value() > self.sp_rangeEnd.value():
            self.sp_rangeEnd.setValue(self.sp_rangeStart.value())

        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def endChanged(self):
        if self.sp_rangeEnd.value() < self.sp_rangeStart.value():
            self.sp_rangeStart.setValue(self.sp_rangeEnd.value())

        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def frameExpressionChanged(self, text=None):
        if not hasattr(self, "expressionWinLabel"):
            return

        frames = self.core.resolveFrameExpression(self.le_frameExpression.text())
        if len(frames) > 1000:
            frames = frames[:1000]
            frames.append("...")

        for idx in range(int(len(frames) / 30.0)):
            frames.insert((idx+1)*30, "\n")

        frameStr = ",".join([str(x) for x in frames]) or "invalid expression"
        self.expressionWinLabel.setText(frameStr)
        self.expressionWin.resize(1, 1)

    @err_catcher(name=__name__)
    def exprMoveEvent(self, event):
        self.showExpressionWin(event)
        if hasattr(self, "expressionWin") and self.expressionWin.isVisible():
            self.expressionWin.move(
                QCursor.pos().x() + 20, QCursor.pos().y() - self.expressionWin.height()
            )
        self.le_frameExpression.origMoveEvent(event)

    @err_catcher(name=__name__)
    def showExpressionWin(self, event):
        if not hasattr(self, "expressionWin") or not self.expressionWin.isVisible():
            if hasattr(self, "expressionWin"):
                self.expressionWin.close()

            self.expressionWin = QFrame()
            ss = getattr(self.core.appPlugin, "getFrameStyleSheet", lambda x: "")(self)
            self.expressionWin.setStyleSheet(
                ss + """ .QFrame{ border: 2px solid rgb(100,100,100);} """
            )

            self.core.parentWindow(self.expressionWin)
            winwidth = 10
            winheight = 10
            VBox = QVBoxLayout()
            frames = self.core.resolveFrameExpression(self.le_frameExpression.text())
            if len(frames) > 1000:
                frames = frames[:1000]
                frames.append("...")

            for idx in range(int(len(frames) / 30.0)):
                frames.insert((idx+1)*30, "\n")

            frameStr = ",".join([str(x) for x in frames]) or "invalid expression"
            self.expressionWinLabel = QLabel(frameStr)
            VBox.addWidget(self.expressionWinLabel)
            self.expressionWin.setLayout(VBox)
            self.expressionWin.setWindowFlags(
                Qt.FramelessWindowHint  # hides the window controls
                | Qt.WindowStaysOnTopHint  # forces window to top... maybe
                | Qt.SplashScreen  # this one hides it from the task bar!
            )

            self.expressionWin.setGeometry(0, 0, winwidth, winheight)
            self.expressionWin.move(QCursor.pos().x() + 20, QCursor.pos().y())
            self.expressionWin.setAttribute(Qt.WA_ShowWithoutActivating)
            self.expressionWin.show()

    @err_catcher(name=__name__)
    def exprLeaveEvent(self, event):
        if hasattr(self, "expressionWin") and self.expressionWin.isVisible():
            self.expressionWin.close()

    @err_catcher(name=__name__)
    def exprFocusOutEvent(self, event):
        if hasattr(self, "expressionWin") and self.expressionWin.isVisible():
            self.expressionWin.close()

    @err_catcher(name=__name__)
    def setCam(self, index):
        self.curCam = self.camlist[index]
        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def nameChanged(self, text):
        text = self.e_name.text()
        context = {}
        context["identifier"] = self.getTaskname() or "None"
        num = 0
        try:
            if "{#}" in text:
                while True:
                    context["#"] = num or ""
                    name = text.format(**context)
                    for state in self.stateManager.states:
                        if state.ui.listType != "Export":
                            continue

                        if state is self.state:
                            continue

                        if state.text(0) == name:
                            num += 1
                            break
                    else:
                        break
            else:
                name = text.format(**context)
        except Exception:
            name = text

        if self.state.text(0).endswith(" - disabled"):
            name += " - disabled"

        self.state.setText(0, name)

    @err_catcher(name=__name__)
    def getFormat(self):
        self.cb_format.currentText()

    @err_catcher(name=__name__)
    def setFormat(self, fmt):
        idx = self.cb_format.findText(fmt)
        if idx != -1:
            self.cb_format.setCurrentIndex(idx)
            self.stateManager.saveStatesToScene()
            return True

        return False

    @err_catcher(name=__name__)
    def getContextType(self):
        contextType = self.cb_context.currentText()
        return contextType

    @err_catcher(name=__name__)
    def setContextType(self, contextType):
        idx = self.cb_context.findText(contextType)
        if idx != -1:
            self.cb_context.setCurrentIndex(idx)
            self.refreshContext()
            return True

        return False

    @err_catcher(name=__name__)
    def getTaskname(self):
        taskName = self.l_taskName.text()
        return taskName

    @err_catcher(name=__name__)
    def setTaskname(self, taskname):
        self.l_taskName.setText(taskname)
        self.setTaskWarn(not bool(taskname))
        self.updateUi()

    @err_catcher(name=__name__)
    def getSortKey(self):
        return self.getTaskname()
    
    # Recursive function where usedlayers is a persistent list which keeps being updated.
    @err_catcher(name=__name__)
    def check_items(self, item, usedlayers:list):
        if item.ui.className == "MHrendLayer":
            layername = item.ui.cb_renderLayer.currentText()
            usedlayers.append(layername)
    
        for i in range(item.childCount()):
            child_item = item.child(i)
            self.check_items(child_item, usedlayers)

    @err_catcher(name=__name__)
    def setRenderLayerCbIndex(self, layername):
        idx = self.cb_renderLayer.findText(layername)
        if idx != -1:  # If the item is found
            self.cb_renderLayer.setCurrentIndex(idx)

    @err_catcher(name=__name__)
    def is_RenderLayerCb_used(self):#->tuple[bool, set]:
        # get the picked layer and set the combobox to the original layer to be iterated over
        chosenname = self.cb_renderLayer.currentText()
        blenderrenderlayers:list = self.pluginMHfunctions.getRenderLayers()
        self.setRenderLayerCbIndex(self.layername)
        treewidget = self.stateManager.tw_export
        remaininglayers:set = set(blenderrenderlayers)
        usedlayers=[]
        for i in range(treewidget.topLevelItemCount()):
            item = treewidget.topLevelItem(i)
            self.check_items(item, usedlayers)
        # make layers unique
        usedlayers = set(usedlayers)
        print("usedlayers: ", usedlayers)
        # If the layer we want to pick has been used, check what layers are remaining to choose from.
        if chosenname in usedlayers:
            renderlayers = set(blenderrenderlayers)
            remaininglayers = renderlayers.difference(usedlayers)
            # set layer to the layer remaining
            return True, remaininglayers
        else:
            return False, remaininglayers

    @err_catcher(name=__name__)
    def on_RenderLayerCb_changed(self, index):
        origname = self.layername
        chosenname = self.cb_renderLayer.currentText()
        # if is not the same one
        if not origname == chosenname:
            isused, arelayersremaining = self.is_RenderLayerCb_used()
            #if the layer is used, dont do anything and show a message, else change the layer to the chosen one
            if isused:
                    message = f"{chosenname} is already being used by another state"
                    self.core.popup(
                        message,
                        title=None,
                        severity="info",
                    )
            else:
                self.setRenderLayerCbIndex(chosenname)
        #set the name of the state and the layername property on the state
        self.layerToTask()
        self.layername = self.cb_renderLayer.currentText()
        self.stateManager.saveStatesToScene()
    
    @err_catcher(name=__name__)
    def ensureUniqueName(self, names):
        seen = {}
        unique_names = []

        for name in names:
            if name in seen:
                seen[name] += 1
                new_name = f"{name}_{seen[name]}"
                while new_name in seen:
                    seen[name] += 1
                    new_name = f"{name}_{seen[name]}"
                unique_names.append(new_name)
                seen[new_name] = 0  # Initialize the new name in the seen dictionary
            else:
                unique_names.append(name)
                seen[name] = 0

        return unique_names[0]

    @err_catcher(name=__name__)
    def createViewLayerDialog(self):
        from PrismUtils import PrismWidgets
        self.nameWin = PrismWidgets.CreateItem(
            startText=self.getTaskname(),
            showTasks=True,
            taskType="3d",
            core=self.core,
        )
        self.core.parentWindow(self.nameWin)
        self.nameWin.setWindowTitle("Create View Layer")
        self.nameWin.l_item.setText("Layer_Name")
        self.nameWin.buttonBox.buttons()[0].setText("Ok")
        self.nameWin.buttonBox.buttons()[1].setVisible(False)
        # self.nameWin.e_item.selectAll()
        result = self.nameWin.exec_()

        if result == 1:
            layerList = self.pluginMHfunctions.getRenderLayers()
            if self.nameWin.e_item.text() in layerList:
                self.ensureUniqueName(layerList)
            self.pluginMHfunctions.createViewLayer(self.nameWin.e_item.text())
            layers = self.pluginMHfunctions.getRenderLayers()
            self.cb_renderLayer.addItems(layers)
            self.on_RenderLayerCb_setup()
            # self.setup(self.state, self.core, self.stateManager)
            self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def on_RenderLayerCb_setup(self):
        if self.core.status == "loaded":
            origname = self.layername
            chosenname = self.cb_renderLayer.currentText()
            isused, remaininglayers = self.is_RenderLayerCb_used()
            # if there are layers to pick from
            if len(remaininglayers) > 0:
                self.setRenderLayerCbIndex(list(remaininglayers)[0])

                self.layerToTask()
                self.layername = self.cb_renderLayer.currentText()
                self.stateManager.saveStatesToScene()
                        
            # if there are not, Modify the layer to be unusable (if possible delete it, but Idk how :) )
            else:
                message = f"there are no layers remaining\n Do you want to create a new layer?"
                result = self.core.popupQuestion(
                    message,
                    title="Create new Layer?",
                )
                if result == "Yes":
                    self.createViewLayerDialog()
                else:
                    self.setTaskname('DELETE THIS STATE')
                    self.gb_passes.setVisible(False)
                    self.gb_layerProperties.setVisible(False)
                    self.gb_output.setVisible(False)
                    self.f_renderLayer.setVisible(False)
                    self.stateManager.saveStatesToScene()

            
    @err_catcher(name=__name__)
    def layerToTask(self):
        layername = self.cb_renderLayer.currentText()
        self.setTaskname(layername)
        self.nameChanged(layername)
        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def changeTask(self):
        from PrismUtils import PrismWidgets
        self.nameWin = PrismWidgets.CreateItem(
            startText=self.getTaskname(),
            showTasks=True,
            taskType="3d",
            core=self.core,
        )
        self.core.parentWindow(self.nameWin)
        self.nameWin.setWindowTitle("Change Identifier")
        self.nameWin.l_item.setText("Identifier:")
        self.nameWin.buttonBox.buttons()[0].setText("Ok")
        self.nameWin.e_item.selectAll()
        result = self.nameWin.exec_()

        if result == 1:
            self.setTaskname(self.nameWin.e_item.text())
            self.nameChanged(self.e_name.text())
            self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def presetOverrideChanged(self, checked):
        self.cb_renderPreset.setEnabled(checked)
        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def resOverrideChanged(self, checked):
        self.sp_resWidth.setEnabled(checked)
        self.sp_resHeight.setEnabled(checked)
        self.b_resPresets.setEnabled(checked)

        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def showResPresets(self):
        pmenu = QMenu(self)

        for preset in self.resolutionPresets:
            pAct = QAction(preset, self)
            res = self.getResolution(preset)
            if not res:
                continue

            pwidth, pheight = res

            pAct.triggered.connect(
                lambda x=None, v=pwidth: self.sp_resWidth.setValue(v)
            )
            pAct.triggered.connect(
                lambda x=None, v=pheight: self.sp_resHeight.setValue(v)
            )
            pAct.triggered.connect(lambda: self.stateManager.saveStatesToScene())
            pmenu.addAction(pAct)

        pmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def getRangeType(self):
        return self.cb_rangeType.currentText()

    @err_catcher(name=__name__)
    def setRangeType(self, rangeType):
        idx = self.cb_rangeType.findText(rangeType)
        if idx != -1:
            self.cb_rangeType.setCurrentIndex(idx)
            self.updateRange()
            return True

        return False

    @err_catcher(name=__name__)
    def getResolution(self, resolution):
        res = None
        if resolution == "Get from rendersettings":
            if hasattr(self.core.appPlugin, "getResolution"):
                res = self.core.appPlugin.getResolution()
            else:
                res = [1920, 1080]
        elif resolution.startswith("Project ("):
            res = resolution[9:-1].split("x")
            res = [int(r) for r in res]
        else:
            try:
                pwidth = int(resolution.split("x")[0])
                pheight = int(resolution.split("x")[1])
                res = [pwidth, pheight]
            except:
                res = getattr(
                    self.core.appPlugin, "evaluateResolution", lambda x: None
                )(resolution)

        return res

    @err_catcher(name=__name__)
    def getMasterVersion(self):
        return self.cb_master.currentText()

    @err_catcher(name=__name__)
    def setMasterVersion(self, master):
        idx = self.cb_master.findText(master)
        if idx != -1:
            self.cb_master.setCurrentIndex(idx)
            self.stateManager.saveStatesToScene()
            return True

        return False

    @err_catcher(name=__name__)
    def getLocation(self):
        return self.cb_outPath.currentText()

    @err_catcher(name=__name__)
    def setLocation(self, location):
        idx = self.cb_outPath.findText(location)
        if idx != -1:
            self.cb_outPath.setCurrentIndex(idx)
            self.stateManager.saveStatesToScene()
            return True

        return False

    
    @err_catcher(name=__name__)
    def sm_toggleLayerNodes(self, *args, **kwargs)->None:
        toggle = self.state.text(0).endswith(" - disabled")
        self.pluginMHfunctions.toggleLayerNodes(self.cb_renderLayer.currentText(), toggle)

    @err_catcher(name=__name__)
    def addPropertyWidget(self, elements):
        for element in elements:
            container = QWidget(self.gb_properties)
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)

            label = QLabel(element, container)
            label.setObjectName(f"label_{element}")
            layout.addWidget(label)

            checkbox = QCheckBox(container)
            checkbox.setObjectName(f"checkbox_{element}")
            checkbox.stateChanged.connect(self.propertyStateChanged)
            layout.addWidget(checkbox)
            
            self.dynamic_checkboxes.append(checkbox)
            self.verticalLayout_11.addWidget(container)

    @err_catcher(name=__name__)
    def propertyStateChanged(self, state):
        checkbox = self.sender()
        element_name = checkbox.objectName().split("_", 1)[1]
        if element_name in self.pluginMHfunctions.layerProperties:
            param = self.pluginMHfunctions.layerProperties[element_name]
            self.pluginMHfunctions.setViewLayerPropertyState(param, self.cb_renderLayer.currentText(), enable=checkbox.isChecked())
        # print(f"Checkbox '{element_name}' changed to {'checked' if state == Qt.Checked else 'unchecked'}")

    @err_catcher(name=__name__)
    def updateLayerProperties(self):
        for chb in self.dynamic_checkboxes:
            element_name = chb.objectName().split("_", 1)[1]
            if element_name in self.pluginMHfunctions.layerProperties:
                param = self.pluginMHfunctions.layerProperties[element_name]
                layername = self.cb_renderLayer.currentText()
                if not layername == "":
                    ischecked = self.pluginMHfunctions.getViewLayerPropertyState(param, layername)
                    chb.setChecked(ischecked)

    @err_catcher(name=__name__)
    def updateUi(self):
        self.w_context.setHidden(not self.allowCustomContext)
        self.refreshContext()

        # update Cams
        self.cb_cam.clear()
        self.camlist = camNames = []

        if not self.stateManager.standalone:
            self.camlist = self.core.appPlugin.getCamNodes(self, cur=True)
            camNames = [self.core.appPlugin.getCamName(self, i) for i in self.camlist]

        self.cb_cam.addItems(camNames)

        if self.curCam in self.camlist:
            self.cb_cam.setCurrentIndex(self.camlist.index(self.curCam))
        else:
            self.cb_cam.setCurrentIndex(0)
            if len(self.camlist) > 0:
                self.curCam = self.camlist[0]
            else:
                self.curCam = None

            self.stateManager.saveStatesToScene()

        self.updateRange()

        if not self.core.mediaProducts.getUseMaster():
            self.w_master.setVisible(False)

        # update Render Layer
        curLayer = self.cb_renderLayer.currentText()
        self.cb_renderLayer.clear()

        layerList = self.pluginMHfunctions.getRenderLayers()
        # layerList = getattr(
        #     self.core.appPlugin, "sm_render_getRenderLayer", lambda x: []
        # )(self)

        self.updateLayerProperties()

        if 'DELETE THIS STATE' in self.l_taskName.text():
            self.cb_renderLayer.clear()
            self.state.setText(0, '!! DELETE THIS STATE !!')
        else:
            self.cb_renderLayer.addItems(layerList)

            if curLayer in layerList:
                self.cb_renderLayer.setCurrentIndex(layerList.index(curLayer))
            else:
                self.cb_renderLayer.setCurrentIndex(0)
                self.stateManager.saveStatesToScene()
            self.layername = self.cb_renderLayer.currentText()

            self.refreshSubmitUi()
            getattr(self.pluginMHfunctions, "sm_render_refreshPasses", lambda x: None)(self)

            self.nameChanged(self.e_name.text())            
            self.isDontUpdateVersionToggled(self.chb_dontUpdateV.isChecked())

        return True

    @err_catcher(name=__name__)
    def refreshContext(self):
        context = self.getCurrentContext()
        contextStr = self.getContextStrFromEntity(context)
        self.l_context.setText(contextStr)

    @err_catcher(name=__name__)
    def getCurrentContext(self):
        context = None
        if self.allowCustomContext:
            ctype = self.getContextType()
            if ctype == "Custom":
                context = self.customContext

        if not context:
            fileName = self.core.getCurrentFileName()
            context = self.core.getScenefileData(fileName)
        
        if "username" in context:
            del context["username"]

        if "user" in context:
            del context["user"]

        return context

    @err_catcher(name=__name__)
    def refreshSubmitUi(self):
        if not self.gb_submit.isHidden():
            if not self.gb_submit.isCheckable():
                return

            submitChecked = self.gb_submit.isChecked()
            for idx in reversed(range(self.gb_submit.layout().count())):
                self.gb_submit.layout().itemAt(idx).widget().setHidden(not submitChecked)

            if submitChecked:
                self.core.plugins.getRenderfarmPlugin(self.cb_manager.currentText()).sm_render_updateUI(self)

    @err_catcher(name=__name__)
    def updateRange(self):
        rangeType = self.cb_rangeType.currentText()
        isCustom = rangeType == "Custom"
        isExp = rangeType == "Expression"
        self.l_rangeStart.setVisible(not isCustom and not isExp)
        self.l_rangeEnd.setVisible(not isCustom and not isExp)
        self.sp_rangeStart.setVisible(isCustom)
        self.sp_rangeEnd.setVisible(isCustom)
        self.w_frameRangeValues.setVisible(False)#(not isExp)
        self.w_frameExpression.setVisible(isExp)

        if not isCustom and not isExp:
            frange = self.getFrameRange(rangeType=rangeType)
            start = str(int(frange[0])) if frange[0] is not None else "-"
            end = str(int(frange[1])) if frange[1] is not None else "-"
            self.l_rangeStart.setText(start)
            self.l_rangeEnd.setText(end)

    @err_catcher(name=__name__)
    def getFrameRange(self, rangeType):
        startFrame = None
        endFrame = None
        if rangeType == "Scene":
            if hasattr(self.core.appPlugin, "getFrameRange"):
                startFrame, endFrame = self.core.appPlugin.getFrameRange(self)
                startFrame = int(startFrame)
                endFrame = int(endFrame)
            else:
                startFrame = 1001
                endFrame = 1100
        elif rangeType == "Shot":
            context = self.getCurrentContext()
            if context.get("type") == "shot" and "sequence" in context:
                frange = self.core.entities.getShotRange(context)
                if frange:
                    startFrame, endFrame = frange
        elif rangeType == "Single Frame":
            if hasattr(self.core.appPlugin, "getCurrentFrame"):
                startFrame = int(self.core.appPlugin.getCurrentFrame())
            else:
                startFrame = 1001
        elif rangeType == "Custom":
            startFrame = self.sp_rangeStart.value()
            endFrame = self.sp_rangeEnd.value()
        elif rangeType == "Expression":
            return self.core.resolveFrameExpression(self.le_frameExpression.text())

        if startFrame == "":
            startFrame = None

        if endFrame == "":
            endFrame = None

        if startFrame is not None:
            startFrame = int(startFrame)

        if endFrame is not None:
            endFrame = int(endFrame)

        return startFrame, endFrame

    @err_catcher(name=__name__)
    def openSlaves(self):
        if eval(os.getenv("PRISM_DEBUG", "False")):
            try:
                del sys.modules["SlaveAssignment"]
            except:
                pass

        import SlaveAssignment

        self.sa = SlaveAssignment.SlaveAssignment(
            core=self.core, curSlaves=self.e_osSlaves.text()
        )
        result = self.sa.exec_()

        if result == 1:
            selSlaves = ""
            if self.sa.rb_exclude.isChecked():
                selSlaves = "exclude "
            if self.sa.rb_all.isChecked():
                selSlaves += "All"
            elif self.sa.rb_group.isChecked():
                selSlaves += "groups: "
                for i in self.sa.activeGroups:
                    selSlaves += i + ", "

                if selSlaves.endswith(", "):
                    selSlaves = selSlaves[:-2]

            elif self.sa.rb_custom.isChecked():
                slavesList = [x.text() for x in self.sa.lw_slaves.selectedItems()]
                for i in slavesList:
                    selSlaves += i + ", "

                if selSlaves.endswith(", "):
                    selSlaves = selSlaves[:-2]

            self.e_osSlaves.setText(selSlaves)
            self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def gpuPtChanged(self):
        self.w_dlGPUdevices.setEnabled(self.sp_dlGPUpt.value() == 0)
        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def gpuDevicesChanged(self):
        self.w_dlGPUpt.setEnabled(self.le_dlGPUdevices.text() == "")
        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def setupNodes(self):
        layername = self.cb_renderLayer.currentText()
        self.pluginMHfunctions.createOutputFromRL(layername=layername)

    @err_catcher(name=__name__)
    def showPasses(self):
        layername = self.cb_renderLayer.currentText()
        steps = getattr(
            self.pluginMHfunctions, "sm_render_getRenderPasses", lambda x, y: None
        )(self, layername)
        

        if steps is None or len(steps) == 0:
            return False

        if self.core.isStr(steps):
            steps = eval(steps)

        if eval(os.getenv("PRISM_DEBUG", "False")):
            try:
                del sys.modules["ItemList"]
            except:
                pass

        import ItemList

        self.il = ItemList.ItemList(core=self.core)
        self.il.setWindowTitle("Select Passes")
        self.core.parentWindow(self.il)
        self.il.tw_steps.doubleClicked.connect(self.il.accept)
        self.il.tw_steps.horizontalHeaderItem(0).setText("Name")
        self.il.tw_steps.setColumnHidden(1, True)
        self.il.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        tech = []
        main = []
        crypto = []
        for i in sorted(steps, key=lambda s: s.lower()):
            passname:str = self.pluginMHfunctions.AOVDict[i.lower()]
            if self.pluginMHfunctions.compareTechPass(passname):
                tech.append(i)
            elif 'crypto' in passname.lower():
                crypto.append(i)
            else:
                main.append(i)
        organizedsteps = tech + main + crypto
        for i in organizedsteps:
            rc = self.il.tw_steps.rowCount()
            self.il.tw_steps.insertRow(rc)
            item1 = QTableWidgetItem(i)            
            passname:str = self.pluginMHfunctions.AOVDict[i.lower()]
            if i in tech:
                item1.setBackground(QColor("#995233"))
            elif i in crypto:
                item1.setBackground(QColor("#429933"))
            else:
                item1.setBackground(QColor("#365e99"))
            self.il.tw_steps.setItem(rc, 0, item1)

        result = self.il.exec_()

        if result != 1:
            return False

        for i in self.il.tw_steps.selectedItems():
            if i.column() == 0:
                self.pluginMHfunctions.sm_render_addRenderPass(
                    self, passName=i.text(), steps=steps, layername=layername
                )

        self.updateUi()
        self.stateManager.saveStatesToScene()
        self.setupNodes()

    @err_catcher(name=__name__)
    def rclickPasses(self, pos):
        if self.lw_passes.currentItem() is None or not getattr(
            self.core.appPlugin, "canDeleteRenderPasses", True
        ):
            return

        rcmenu = QMenu()

        delAct = QAction("Delete", self)
        delAct.triggered.connect(self.deleteAOVs)
        rcmenu.addAction(delAct)

        rcmenu.exec_(QCursor.pos())

    @err_catcher(name=__name__)
    def deleteAOVs(self):
        items = self.lw_passes.selectedItems()
        for i in items:
            self.pluginMHfunctions.removeAOV(i.text(), self.cb_renderLayer.currentText())
        self.pluginMHfunctions.removeEmptyOutNodes(self.cb_renderLayer.currentText())
        # self.pluginMHfunctions.repositionLayerOutNodes(self.cb_renderLayer.currentText())
        self.pluginMHfunctions.repositionRenderLayerNodes()
        self.updateUi()

    @err_catcher(name=__name__)
    def rjToggled(self, checked):
        self.refreshSubmitUi()
        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def managerChanged(self, text=None):
        plugin = self.core.plugins.getRenderfarmPlugin(self.cb_manager.currentText())
        if plugin:
            plugin.sm_render_managerChanged(self)

        self.stateManager.saveStatesToScene()

    @err_catcher(name=__name__)
    def getContextStrFromEntity(self, entity):
        if not entity:
            return ""

        entityType = entity.get("type", "")
        if entityType == "asset":
            entityName = entity.get("asset_path").replace("\\", "/")
        elif entityType == "shot":
            entityName = self.core.entities.getShotName(entity)
        else:
            return ""

        context = "%s - %s" % (entityType.capitalize(), entityName)
        return context

    @err_catcher(name=__name__)
    def preExecuteState(self):
        warnings = []

        self.updateUi()

        # if self.tasknameRequired and not self.getTaskname():
        #     warnings.append(["No identifier is given.", "", 3])

        # if self.curCam is None or (
        #     self.curCam != "Current View"
        #     and not self.core.appPlugin.isNodeValid(self, self.curCam)
        # ):
        #     warnings.append(["No camera is selected.", "", 3])
        # elif self.curCam == "Current View":
        #     warnings.append(["No camera is selected.", "", 2])

        # rangeType = self.cb_rangeType.currentText()
        # frames = self.getFrameRange(rangeType)
        # if rangeType != "Expression":
        #     frames = frames[0]

        # if frames is None or frames == []:
        #     warnings.append(["Framerange is invalid.", "", 3])

        # if not self.gb_submit.isHidden() and self.gb_submit.isChecked():
        #     plugin = self.core.plugins.getRenderfarmPlugin(self.cb_manager.currentText())
        #     warnings += plugin.sm_render_preExecute(self)

        warnings += self.core.appPlugin.sm_render_preExecute(self)

        return [self.state.text(0), warnings]

    @err_catcher(name=__name__)
    def getOutputName(self, useVersion="next"):
        if self.tasknameRequired and not self.getTaskname():
            return

        task = self.getTaskname()
        extension = self.cb_format.currentText()
        context = self.getCurrentContext()
        framePadding = ""

        if "type" not in context:
            return

        singleFrame = self.cb_rangeType.currentText() == "Single Frame"
        location = self.cb_outPath.currentText()
        outputPathData = self.core.mediaProducts.generateMediaProductPath(
            entity=context,
            task=task,
            extension=extension,
            framePadding=framePadding,
            comment=self.stateManager.publishComment,
            version=useVersion if useVersion != "next" else None,
            location=location,
            singleFrame=singleFrame,
            returnDetails=True,
            mediaType=self.mediaType,
            state=self,
        )

        outputFolder = os.path.dirname(outputPathData["path"])
        hVersion = outputPathData["version"]

        return outputPathData["path"], outputFolder, hVersion

    @err_catcher(name=__name__)
    def executeState(self, parent, useVersion="next", calledFromMHRender=False)->None:
        willexecute = True
        layerhasoutnodes = False
        result = "Result=Success"
        # check if there are nodes asociated to this layer.
        rlayername = self.cb_renderLayer.currentText()
        layers = self.pluginMHfunctions.getRenderLayers()
        if rlayername in layers:
            outnodesdict:dict = self.pluginMHfunctions.getLayerOutNodes(rlayername)
            for v in list(outnodesdict.values()):
                if v:
                    layerhasoutnodes = True
                    break
        if layerhasoutnodes:
            # if dont update version is checked and there is a path already.
            print("l_pathLast.text(): ", self.l_pathLast.text())
            if self.chb_dontUpdateV.isChecked() and self.l_pathLast.text() != None:
                willexecute = False
            
            if willexecute:

                updateMaster = True
                fileName = self.core.getCurrentFileName()
                context = self.getCurrentContext()
                if not self.renderingStarted:
                    if self.tasknameRequired and not self.getTaskname():
                        return [
                            self.state.text(0)
                            + ": error - no identifier is given. Skipped the activation of this state."
                        ]
            
                    outputName, outputPath, hVersion = self.getOutputName(useVersion=useVersion)
                    print("outputName: ", outputName, "outputPath: ",outputPath, "hVersion: ", hVersion)
                    expandedOutputPath = os.path.expandvars(outputPath)
                    print("expanded output path: ", expandedOutputPath)
                    outLength = len(outputName)
                    if platform.system() == "Windows" and os.getenv("PRISM_IGNORE_PATH_LENGTH") != "1" and outLength > 255:
                        return [
                            self.state.text(0)
                            + " - error - The outputpath is longer than 255 characters (%s), which is not supported on Windows. Please shorten the outputpath by changing the comment, taskname or projectpath."
                            % outLength
                        ]

                    if not os.path.exists(os.path.dirname(expandedOutputPath)):
                        os.makedirs(os.path.dirname(expandedOutputPath))

                    details = context.copy()
                    if "filename" in details:
                        del details["filename"]

                    if "extension" in details:
                        del details["extension"]

                    details["version"] = hVersion
                    details["sourceScene"] = fileName
                    details["identifier"] = self.getTaskname()
                    details["comment"] = self.stateManager.publishComment

                    if self.mediaType == "3drenders":
                        infopath = os.path.dirname(expandedOutputPath)
                    else:
                        infopath = expandedOutputPath

                    self.core.saveVersionInfo(
                        filepath=infopath, details=details
                    )
                    
                    self.pluginMHfunctions.setOutputsPaths(self.cb_renderLayer.currentText(), expandedOutputPath)
                    
                    # the aov is necesary for prism logic, we have to remove it fo some of our operations.
                    outputpathnoaov = os.path.join(os.path.dirname(expandedOutputPath),os.path.basename(outputName))

                    self.l_pathLast.setText(outputpathnoaov)
                    self.l_pathLast.setToolTip(outputpathnoaov)
                    self.stateManager.saveStatesToScene()

                    pathassigned = True
                    if rlayername in layers:
                        outnodesdict:dict = self.pluginMHfunctions.getLayerOutNodes(rlayername)
                        for node in list(outnodesdict.values()):
                            if not os.path.dirname(expandedOutputPath) in node.base_path:
                                pathassigned = False

                    if pathassigned:
                        result = "Result=Success"
                    else:
                        result = " - error - The outputpath was not assigned to nodes."
                    
                else:
                    result = "Result=Success"

                # if result == "publish paused":
                #     return [self.state.text(0) + " - publish paused"]
                # else:
                #     if updateMaster:
                #         self.handleMasterVersion(os.path.expandvars(outputName))
                
                if not calledFromMHRender:
                    if result=="Result=Success":
                        msgStr = "The Execution was successful."
                        self.core.popup(msgStr, title="Execute", severity="info",)
                    elif "error" in result:
                        msgStr = result.replace(" - error - ", "")
                        self.core.popup(msgStr, title="Execute Error", severity="info",)
                    
            else:
                if not calledFromMHRender:
                    message = "Don't update Version is toggled ON\nthe paths on nodes were not updated"
                    self.core.popup(message,title=None,severity="info",)
        else:
            message = "This Layer has no File Output nodes\nasociated with it."
            self.core.popup(message,title=None,severity="info",)
        
        ### RETURN ###
        if "Result=Success" in result:
            return [self.state.text(0) + " - success"]
        else:
            erStr = "%s ERROR - sm_default_imageRenderPublish %s:\n%s" % (
                time.strftime("%d/%m/%y %X"),
                self.core.version,
                result,
            )
            if not result.startswith("Execute Canceled: "):
                self.core.writeErrorLog(erStr)
            return [self.state.text(0) + " - error - " + result]

    @err_catcher(name=__name__)
    def isUsingMasterVersion(self):
        useMaster = self.core.mediaProducts.getUseMaster()
        if not useMaster:
            return False

        masterAction = self.cb_master.currentText()
        if masterAction == "Don't update master":
            return False

        return True

    @err_catcher(name=__name__)
    def handleMasterVersion(self, outputName):
        if not self.isUsingMasterVersion():
            return

        masterAction = self.cb_master.currentText()
        if masterAction == "Set as master":
            self.core.mediaProducts.updateMasterVersion(outputName)
        elif masterAction == "Add to master":
            self.core.mediaProducts.addToMasterVersion(outputName)

    @err_catcher(name=__name__)
    def setTaskWarn(self, warn):
        useSS = getattr(self.core.appPlugin, "colorButtonWithStyleSheet", False)
        if warn:
            if useSS:
                self.b_changeTask.setStyleSheet(
                    "QPushButton { background-color: rgb(200,0,0); }"
                )
            else:
                self.b_changeTask.setPalette(self.warnPalette)
        else:
            if useSS:
                self.b_changeTask.setStyleSheet("")
            else:
                self.b_changeTask.setPalette(self.oldPalette)

    @err_catcher(name=__name__)
    def getStateProps(self):
        stateProps = {
            "stateName": self.e_name.text(),
            "contextType": self.getContextType(),
            "customContext": self.customContext,
            "taskname": self.getTaskname(),
            "renderpresetoverride": str(self.chb_renderPreset.isChecked()),
            "currentrenderpreset": self.cb_renderPreset.currentText(),
            "rangeType": str(self.cb_rangeType.currentText()),
            "startframe": self.sp_rangeStart.value(),
            "endframe": self.sp_rangeEnd.value(),
            "frameExpression": self.le_frameExpression.text(),
            "currentcam": str(self.curCam),
            "resoverride": str(
                [
                    self.chb_resOverride.isChecked(),
                    self.sp_resWidth.value(),
                    self.sp_resHeight.value(),
                ]
            ),
            "masterVersion": self.cb_master.currentText(),
            "curoutputpath": self.cb_outPath.currentText(),
            "renderlayer": str(self.cb_renderLayer.currentText()),
            "outputFormat": str(self.cb_format.currentText()),
            "submitrender": str(self.gb_submit.isChecked()),
            "rjmanager": str(self.cb_manager.currentText()),
            "rjprio": self.sp_rjPrio.value(),
            "rjframespertask": self.sp_rjFramesPerTask.value(),
            "rjtimeout": self.sp_rjTimeout.value(),
            "rjsuspended": str(self.chb_rjSuspended.isChecked()),
            "osdependencies": str(self.chb_osDependencies.isChecked()),
            "osupload": str(self.chb_osUpload.isChecked()),
            "ospassets": str(self.chb_osPAssets.isChecked()),
            "osslaves": self.e_osSlaves.text(),
            "dlconcurrent": self.sp_dlConcurrentTasks.value(),
            "dlgpupt": self.sp_dlGPUpt.value(),
            "dlgpudevices": self.le_dlGPUdevices.text(),
            "lastexportpath": self.l_pathLast.text().replace("\\", "/"),
            "enablepasses": str(self.gb_passes.isChecked()),
            "stateenabled": self.core.getCheckStateValue(self.state.checkState(0)),
            "dontupdateversion":str(self.chb_dontUpdateV.isChecked()),
        }
        self.core.callback("onStateGetSettings", self, stateProps)
        return stateProps
