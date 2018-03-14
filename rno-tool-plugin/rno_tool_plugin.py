# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RnoToolPlugin
                                 A QGIS plugin
 怡创网优工具
                              -------------------
        begin                : 2017-10-11
        git sha              : $Format:%H$
        copyright            : (C) 2017 by HGICRAETE
        email                : xiao.sz@hgicreate.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import math
import qgis
import xlrd
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QColor, QMessageBox
# Initialize Qt resources from file resources.py
from qgis._core import QgsField, QgsMapLayerRegistry, QgsVectorLayer, QgsFeature, QgsSymbolV2, QgsRendererCategoryV2, \
    QgsPoint, QgsGeometry, QgsCategorizedSymbolRendererV2, QgsPalLayerSettings

import resources
# Import the code for the dialog
from GSMFreqSearch import GSMFreqSearch
from LTEFreqPCISearch import LTEFreqPCISearch
from rno_tool_plugin_dialog import RnoToolPluginDialog
import os.path


class RnoToolPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'RnoToolPlugin_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = RnoToolPluginDialog()
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Rno Tool Plugin')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'怡创网优工具')
        self.toolbar.setObjectName(u'怡创网优工具')


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('RnoToolPlugin', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """



        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/RnoToolPlugin/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Rno Tool Plugin'),
            callback=self.run,
            parent=self.iface.mainWindow())
        self.dlg.progressBar.setVisible(False)
        self.dlg.lineEdit.clear()
        self.dlg.inputCRS.clear()
        self.dlg.PickFileButton.clicked.connect(self.select_input_file)
        self.dlg.G4Button.clicked.connect(self.onG4ButtonClick)
        self.dlg.G3Button.clicked.connect(self.onG3ButtonClick)
        self.dlg.G2Button.clicked.connect(self.onG2ButtonClick)
        self.dlg.CancelButton.clicked.connect(self.onCancelButtonClick)
        self.dlg.GSMFreqSearchBtn.clicked.connect(self.GSMFreqSearchBtn)
        self.dlg.LTEFreqPCISearchBtn.clicked.connect(self.LTEFreqPCISearchBtn)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Rno Tool Plugin'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def select_input_file(self):
        self.filename = QFileDialog.getOpenFileName(self.dlg, u"选择打开文件", self.storedLastFilePathLine[1], "")
        self.dlg.lineEdit.setText(self.filename)

    def onG4ButtonClick(self):
        filename = self.dlg.lineEdit.text()
        if filename.endswith(u'.xls') | filename.endswith(u'.xlsx'):
            # self.run(filename)
            self.dlg.G4Button.setEnabled(False)
            self.dlg.PickFileButton.setEnabled(False)
            data = self.openFile(filename)
            self.painting(data, '4G')
        else:
            self.showErrorDialog(u'文档格式错误', u'请选择Excel工作簿进行打开')
        self.dlg.G4Button.setEnabled(True)
        self.dlg.PickFileButton.setEnabled(True)
        self.dlg.progressBar.setValue(0)
        self.dlg.progressBar.setVisible(False)

    def onG3ButtonClick(self):
        filename = self.dlg.lineEdit.text()
        if filename.endswith(u'.xls') | filename.endswith(u'.xlsx'):
            # self.run(filename)
            self.dlg.G3Button.setEnabled(False)
            self.dlg.PickFileButton.setEnabled(False)
            data = self.openFile(filename)
            self.painting(data, '3G')
        else:
            self.showErrorDialog(u'文档格式错误', u'请选择Excel工作簿进行打开')
        self.dlg.G3Button.setEnabled(True)
        self.dlg.PickFileButton.setEnabled(True)
        self.dlg.progressBar.setValue(0)
        self.dlg.progressBar.setVisible(False)

    def onG2ButtonClick(self):
        filename = self.dlg.lineEdit.text()
        if filename.endswith(u'.xls') | filename.endswith(u'.xlsx'):
            # self.run(filename)
            self.dlg.G2Button.setEnabled(False)
            self.dlg.PickFileButton.setEnabled(False)
            data = self.openFile(filename)
            self.painting(data, '2G')
        else:
            self.showErrorDialog(u'文档格式错误', u'请选择Excel工作簿进行打开')
        self.dlg.G2Button.setEnabled(True)
        self.dlg.PickFileButton.setEnabled(True)
        self.dlg.progressBar.setValue(0)
        self.dlg.progressBar.setVisible(False)

    def onCancelButtonClick(self):
        self.dlg.G4Button.setEnabled(True)
        self.dlg.G3Button.setEnabled(True)
        self.dlg.G2Button.setEnabled(True)
        self.dlg.PickFileButton.setEnabled(True)
        self.dlg.progressBar.setValue(0)
        self.dlg.progressBar.setVisible(False)
        self.dlg.close()

    def GSMFreqSearchBtn(self):
        self.gsmfsdlg = GSMFreqSearch()
        self.gsmfsdlg.OKButton.clicked.connect(self.gsmfsOKBtn)
        self.gsmfsdlg.exec_()

    def gsmfsOKBtn(self):

        currentInputCRS = self.dlg.inputCRS.text().replace(" ", "")

        inputFreq = self.gsmfsdlg.inputFreq.text()
        try:
            sourceLayer = QgsMapLayerRegistry.instance().mapLayersByName(u'2G基础信息图层')[0]
        except:
            self.showErrorDialog(u'未找到图层', u'请检查是否已加载“2G基础信息图层”')
            return

        # 隐藏之前的同名图层
        try:
            sameLayer = QgsMapLayerRegistry.instance().mapLayersByName(u'2G图层频点查找')
            for oneLayer in sameLayer:
                qgis.utils.iface.legendInterface().setLayerVisible(oneLayer, False)
        except:
            pass
        gsmfsLayer = QgsVectorLayer("Polygon?crs=EPSG:"+currentInputCRS, u"2G图层频点查找", "memory")
        gsmfsPr = gsmfsLayer.dataProvider()
        gsmfsPr.addAttributes(self.createAttributesTable('2GFreqSearch'))
        gsmfsLayer.updateFields()

        # QgsMapLayerRegistry.instance().addMapLayer(gsmfsLayer)
        qgis.utils.iface.legendInterface().setLayerVisible(sourceLayer, False)
        gsmfsFet = QgsFeature()
        try:
            inputFreq.replace(" ", "")
            B = int(inputFreq)
        except:
            self.showErrorDialog(u'错误的输入', u'请输入数字')
            return
        A = B - 1
        C = B + 1
        PCI_Types = {
            A: ('#FF63F2', u'频点='+ str(A)),
            B: ('#FFFF00', u'指定频点='+ str(B)),
            C: ('#01FF8D', u'频点='+ str(C)),
            '-1': ('#eeeeee', u'无关频点')
        }
        categories = []
        for pci_type, (color, label) in PCI_Types.items():
            symbol = QgsSymbolV2.defaultSymbol(gsmfsLayer.geometryType())
            symbol.setColor(QColor(color))
            category = QgsRendererCategoryV2(pci_type, symbol, label)
            categories.append(category)

        # 创建属性表
        fetAttrs = []
        relatedAttrs = []
        Longitude, Latitude, Azimuth = 15, 16, 5
        for feature in sourceLayer.getFeatures():
            attrs = feature.attributes()
            if (int(inputFreq) == attrs[3]):
                temp = []
                for j in range(67):
                    temp.append(attrs[j])
                temp.append(B)
                relatedAttrs.append(temp)
            elif int(inputFreq) == int(attrs[3]) - 1:
                temp = []
                for j in range(67):
                    temp.append(attrs[j])
                temp.append(A)
                relatedAttrs.append(temp)
            elif int(inputFreq) == int(attrs[3]) + 1:
                temp = []
                for j in range(67):
                    temp.append(attrs[j])
                temp.append(C)
                relatedAttrs.append(temp)
            else:
                temp = []
                for j in range(67):
                    temp.append(attrs[j])
                    if j == 66:
                        if (int(inputFreq) != attrs[3]) & (int(inputFreq) != int(attrs[3])-1) & (int(inputFreq) != int(attrs[3])+1):
                            temp.append('-1')
                fetAttrs.append(temp)
        for one in relatedAttrs:
            fetAttrs.append(one)
        for fetAttr in fetAttrs:
            gsmfsFet.setAttributes(fetAttr)
            #开始画图
            points = [QgsPoint(fetAttr[Longitude], fetAttr[Latitude])]  # start point
            startAngle = -20
            endAngle = 20
            while startAngle <= endAngle:
                points.append(QgsPoint(fetAttr[Longitude] + 0.001 * math.sin(math.radians(fetAttr[Azimuth] + startAngle)),
                                       fetAttr[Latitude] + 0.001 * math.cos(math.radians(fetAttr[Azimuth] + startAngle))))
                startAngle += 2
            points.append(QgsPoint(fetAttr[Longitude], fetAttr[Latitude]))  # end point
            gsmfsFet.setGeometry(QgsGeometry.fromPolygon([points]))
            gsmfsPr.addFeatures([gsmfsFet])
            #根据字段值渲染颜色
            expression = 'Condition'  # field name
            renderer = QgsCategorizedSymbolRendererV2(expression, categories)
            gsmfsLayer.setRendererV2(renderer)

            gsmfsLayer.updateExtents()
            gsmfsLayer.commitChanges()
            gsmfsLayer.updateFields()
            QgsMapLayerRegistry.instance().addMapLayer(gsmfsLayer)
        self.gsmfsdlg.close()
        self.saveEPSGChange()
        self.dlg.close()

    def LTEFreqPCISearchBtn(self):
        self.ltefpsdlg = LTEFreqPCISearch()
        self.ltefpsdlg.OKButton.clicked.connect(self.ltefpsOKBtn)
        self.ltefpsdlg.exec_()

    def ltefpsOKBtn(self):
        currentInputCRS = self.dlg.inputCRS.text().replace(" ", "")
        try:
            sourceLayer = QgsMapLayerRegistry.instance().mapLayersByName(u'4G基础信息图层')[0]
        except:
            self.showErrorDialog(u'未找到图层', u'请检查是否已加载“4G基础信息图层”')
            return
        try:
            inputFreq = int(self.ltefpsdlg.inputFreq.text())
            inputPCI = int(self.ltefpsdlg.inputPCI.text())
        except:
            self.showErrorDialog(u'错误的输入', u'请输入数字')
            return

        # 隐藏之前的同名图层
        try:
            sameLayers = QgsMapLayerRegistry.instance().mapLayersByName(u'4G图层频点PCI查找')
            for oneLayer in sameLayers:
                qgis.utils.iface.legendInterface().setLayerVisible(oneLayer, False)
        except:
            pass

        ltefpsLayer = QgsVectorLayer("Polygon?crs=EPSG:"+currentInputCRS, u"4G图层频点PCI查找", "memory")
        ltefpsPr = ltefpsLayer.dataProvider()
        ltefpsPr.addAttributes(self.createAttributesTable('4GFreqPCISearch'))
        ltefpsLayer.updateFields()
        qgis.utils.iface.legendInterface().setLayerVisible(sourceLayer, False)
        ltefpsFet = QgsFeature()

        PCI_Types = {
            1: ('#FFFF00', u'频点='+str(inputFreq)+',PCI='+str(inputPCI)),
            0: ('#EEEEEE', u'无关频点PCI')
        }
        categories = []
        for pci_type, (color, label) in PCI_Types.items():
            symbol = QgsSymbolV2.defaultSymbol(ltefpsLayer.geometryType())
            symbol.setColor(QColor(color))
            category = QgsRendererCategoryV2(pci_type, symbol, label)
            categories.append(category)
            # 创建属性表
            fetAttrs = []
            relatedAttrs = []
            Longitude, Latitude, Azimuth = 11, 12, 14
            for feature in sourceLayer.getFeatures():
                attrs = feature.attributes()
                if (inputFreq == attrs[9]) & (inputPCI == int(attrs[13])):
                    temp = []
                    for j in range(21):
                        temp.append(attrs[j])
                    temp.append(1)
                    relatedAttrs.append(temp)
                else:
                    temp = []
                    for j in range(21):
                        temp.append(attrs[j])
                    temp.append(0)
                    fetAttrs.append(temp)
            for one in relatedAttrs:
                fetAttrs.append(one)
            for fetAttr in fetAttrs:
                ltefpsFet.setAttributes(fetAttr)
                # 开始画图
                points = [QgsPoint(fetAttr[Longitude], fetAttr[Latitude])]  # start point
                startAngle = -20
                endAngle = 20
                while startAngle <= endAngle:
                    points.append(
                        QgsPoint(fetAttr[Longitude] + 0.001 * math.sin(math.radians(fetAttr[Azimuth] + startAngle)),
                                 fetAttr[Latitude] + 0.001 * math.cos(math.radians(fetAttr[Azimuth] + startAngle))))
                    startAngle += 2
                points.append(QgsPoint(fetAttr[Longitude], fetAttr[Latitude]))  # end point
                ltefpsFet.setGeometry(QgsGeometry.fromPolygon([points]))
                ltefpsPr.addFeatures([ltefpsFet])
                # 根据字段值渲染颜色
                expression = 'FreqPCI'  # field name
                renderer = QgsCategorizedSymbolRendererV2(expression, categories)
                ltefpsLayer.setRendererV2(renderer)

                ltefpsLayer.updateExtents()
                ltefpsLayer.commitChanges()
                ltefpsLayer.updateFields()
                # 更新图层
                QgsMapLayerRegistry.instance().addMapLayer(ltefpsLayer)
        self.ltefpsdlg.close()
        self.saveEPSGChange()
        self.dlg.close()

    def showErrorDialog(self, title, content):
        messageBox = QMessageBox()
        messageBox.setWindowTitle(title)
        messageBox.setText(content)
        messageBox.setIcon(QMessageBox.Critical)
        messageBox.exec_()

    def openFile(self, filename):
        try:
            data = xlrd.open_workbook(filename)
            self.dlg.lineEdit.setText('')
            return data
        except:
            self.showErrorDialog(u'文档打开出错', u'文档可能存在错误')

    def painting(self, data, fileType):
        currentInputCRS = self.dlg.inputCRS.text().replace(" ", "")
        table = data.sheets()[0]
        nrows = table.nrows
        if fileType == '4G':
            vl = QgsVectorLayer("Polygon?crs=EPSG:"+currentInputCRS, u"4G基础信息图层", "memory")
            vlLabel = QgsVectorLayer("Polygon?crs=EPSG:"+currentInputCRS, u"4G基础信息标签层", "memory")
        elif fileType == '3G':
            vl = QgsVectorLayer("Polygon?crs=EPSG:"+currentInputCRS, u"3G基础信息图层", "memory")
            vlLabel = QgsVectorLayer("Polygon?crs=EPSG:"+currentInputCRS, u"3G基础信息标签层", "memory")
        elif fileType == '2G':
            vl = QgsVectorLayer("Polygon?crs=EPSG:"+currentInputCRS, u"2G基础信息图层", "memory")
            vlLabel = QgsVectorLayer("Polygon?crs=EPSG:"+currentInputCRS, u"2G基础信息标签层", "memory")

        pr = vl.dataProvider()
        vlLabelPr = vlLabel.dataProvider()

        attrs = self.createAttributesTable(fileType)

        pr.addAttributes(attrs)
        vlLabelPr.addAttributes(attrs)
        vl.updateFields()
        vlLabel.updateFields()

        fet = QgsFeature()
        self.dlg.progressBar.setVisible(True)
        '''开始读取到内存'''
        list = [[] for row in range(nrows-1)]
        for i in range(nrows):
            if i > 0:
                try:
                    if fileType == '4G':
                        for j in range(21):
                             list[i - 1].append(table.cell(i, j).value)
                             if j == 20:
                                 list[i - 1].append(table.cell(i, 13).value % 3)
                    if fileType == '3G':
                        for j in range(73):
                             list[i - 1].append(table.cell(i, j).value)
                             if j == 72:
                                 list[i - 1].append(int(table.cell(i, 5).value) % 3)
                    if fileType =='2G':
                        for j in range(67):
                             list[i - 1].append(table.cell(i, j).value)
                             if j == 66:
                                 list[i - 1].append(int(table.cell(i, 2).value) % 3)
                except:
                    self.showErrorDialog(u'文档读取出错', u'文档可能存在错误或格式不符合规范')
                    self.dlg.progressBar.setVisible(False)
                    return
        '''完成读取到内存'''

        PCI_Types = {
            '0': ('#F49ECC', 'Mod3=0'),
            '1': ('#65F0FF', 'Mod3=1'),
            '2': ('#00FF00', 'Mod3=2'),
            '3': ('#000', u'未知值'),
        }
        categories = []
        for pci_type, (color, label) in PCI_Types.items():
            symbol = QgsSymbolV2.defaultSymbol(vl.geometryType())
            # symbol = QgsFillSymbolV2.createSimple({'color': color, 'color_border': color, 'width_border': '2'})
            symbol.setColor(QColor(color))
            # symbol.symbolLayer(0).setOutlineColor(QColor('#75263b'))
            category = QgsRendererCategoryV2(pci_type, symbol, label)
            categories.append(category)

        for i in range(len(list)):
            fetAttrs =[]
            if fileType == '4G':
                for j in range(22):
                    fetAttrs.append(list[i][j])
            elif fileType == '3G':
                for j in range(74):
                    fetAttrs.append(list[i][j])
            elif fileType == '2G':
                for j in range(68):
                    fetAttrs.append(list[i][j])
            fet.setAttributes(fetAttrs)
            if fileType == '4G':
                Longitude = 11
                Latitude = 12
                Azimuth = list[i][14]
            elif fileType == '3G':
                Longitude = 12
                Latitude = 13
                Azimuth = list[i][15]
            elif fileType == '2G':
                Longitude = 15
                Latitude = 16
                Azimuth = list[i][5]

            points = [QgsPoint(list[i][Longitude], list[i][Latitude])]  # start point
            startAngle = -20
            endAngle = 20
            while startAngle <= endAngle:
                # midway points
                points.append(QgsPoint(list[i][Longitude] + 0.001 * math.sin(math.radians(Azimuth + startAngle)),
                                       list[i][Latitude] + 0.001 * math.cos(math.radians(Azimuth + startAngle))))
                startAngle += 2
            points.append(QgsPoint(list[i][Longitude], list[i][Latitude]))  # end point

            # create the renderer and assign it to a layer
            expression = 'Mod3'  # field name
            renderer = QgsCategorizedSymbolRendererV2(expression, categories)
            vl.setRendererV2(renderer)

            fet.setGeometry(QgsGeometry.fromPolygon([points]))
            pr.addFeatures([fet])

            # fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(Longitude, Latitude)))
            vlLabelPr.addFeatures([fet])

            vlLabel.setLayerTransparency(100)

            vl.updateExtents()
            vlLabel.updateExtents()
            vl.commitChanges()
            vlLabel.commitChanges()
            vl.updateFields()
            vlLabel.updateFields()
            if i % 200 == 0:
                print 'progress:', float(pr.featureCount()) / nrows * 100
                self.dlg.progressBar.setValue(float(pr.featureCount()) / nrows * 100.0)

            palyr = QgsPalLayerSettings()
            # palyr.readFromLayer(vl)
            palyr.enabled = True
            palyr.fieldName = 'CellName'
            if fileType =='2G':
                palyr.fieldName = 'CELL_NAME'
            palyr.placement = QgsPalLayerSettings.OverPoint
            # palyr.setDataDefinedProperty(QgsPalLayerSettings.Size,False,False,'','')
            palyr.writeToLayer(vlLabel)
            QgsMapLayerRegistry.instance().addMapLayer(vl)
            QgsMapLayerRegistry.instance().addMapLayer(vlLabel)
        print 'progress:', 100
        self.dlg.progressBar.setValue(0)
        self.dlg.progressBar.setVisible(False)
        self.iface.messageBar().clearWidgets()
        qgis.utils.iface.setActiveLayer(vl)
        self.saveEPSGChange()
        self.dlg.close()

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()

        self.filename = ''
        # 读取或新建配置文件
        basepath = os.path.dirname(os.path.realpath(__file__))
        settingsFile = os.path.join(basepath, 'settings.ini')
        try:
            setting = open(settingsFile, 'r')
            a = setting.readline()
            if len(a) <= 0:
                # 设置默认EPSG=4326
                setting.close()
                setting = open(settingsFile, 'w')
                setting.write("EPSG=4326\n")
                setting.write("LastFilePath=C:/")
                setting.close()
            else:
                setting.close()
        except:
            setting = open(settingsFile, 'w')
            setting.write("EPSG=4326\n")
            setting.write("LastFilePath=C:/")
            setting.close()
        setting = open(settingsFile, 'r')
        CRSLine = setting.readline().decode('utf-8')
        self.storedCRS = CRSLine.split("=")
        self.dlg.inputCRS.setText(self.storedCRS[1].replace("\n", ""))
        LastFilePathLine = setting.readline().decode('utf-8')
        self.storedLastFilePathLine = LastFilePathLine.split("=")
        setting.close()
        self.filename = self.storedLastFilePathLine[1].replace(" ", "")

        # Run the dialog event loop
        self.dlg.lineEdit.setText('')
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            pass

    def createAttributesTable(self, fileType):
        if fileType == '4G':
            attrs = [
                QgsField("TAC", QVariant.Int),
                QgsField("eNbID", QVariant.Int),
                QgsField("MEID", QVariant.Int),
                QgsField("eNbName", QVariant.String),
                QgsField("MEID-CellName", QVariant.String),
                QgsField(u"区域", QVariant.String),
                QgsField("CellID", QVariant.Int),
                QgsField("CellName", QVariant.String),
                QgsField(u"频点属性", QVariant.String),
                QgsField("Freq", QVariant.Int),
                QgsField("SiteType", QVariant.String),
                QgsField("Longitude", QVariant.Double),
                QgsField("Latitude", QVariant.Double),
                QgsField("PCI", QVariant.Int),
                QgsField("Azimuth", QVariant.Int),
                QgsField("DownTilt", QVariant.Int),
                QgsField("BeamWidth", QVariant.Int),
                QgsField("CRS", QVariant.Int),
                QgsField("IP", QVariant.Int),
                QgsField(u"网格", QVariant.Int),
                QgsField(u"是否维护", QVariant.Int),
                QgsField("Mod3", QVariant.Int),
            ]
            return attrs
        elif fileType == '4GFreqPCISearch':
            attrs = [
                QgsField("TAC", QVariant.Int),
                QgsField("eNbID", QVariant.Int),
                QgsField("MEID", QVariant.Int),
                QgsField("eNbName", QVariant.String),
                QgsField("MEID-CellName", QVariant.String),
                QgsField(u"区域", QVariant.String),
                QgsField("CellID", QVariant.Int),
                QgsField("CellName", QVariant.String),
                QgsField(u"频点属性", QVariant.String),
                QgsField("Freq", QVariant.Int),
                QgsField("SiteType", QVariant.String),
                QgsField("Longitude", QVariant.Double),
                QgsField("Latitude", QVariant.Double),
                QgsField("PCI", QVariant.Int),
                QgsField("Azimuth", QVariant.Int),
                QgsField("DownTilt", QVariant.Int),
                QgsField("BeamWidth", QVariant.Int),
                QgsField("CRS", QVariant.Int),
                QgsField("IP", QVariant.Int),
                QgsField(u"网格", QVariant.Int),
                QgsField(u"是否维护", QVariant.Int),
                QgsField("FreqPCI", QVariant.Int),
            ]
            return attrs
        elif fileType == '3G':
            attrs = [
                QgsField("MCC", QVariant.Int),
                QgsField("MNC", QVariant.Int),
                QgsField("RNCID", QVariant.Int),
                QgsField("SiteName", QVariant.String),
                QgsField("CellName", QVariant.String),
                QgsField("CellID", QVariant.Int),
                QgsField("NodeBID", QVariant.Int),
                QgsField("CellParameterID", QVariant.Int),
                QgsField("Sector", QVariant.Int),
                QgsField("LAC", QVariant.Int),
                QgsField("RAC", QVariant.Int),
                QgsField("CI", QVariant.Int),
                QgsField("Longitude", QVariant.Double),
                QgsField("Latitude", QVariant.Double),
                QgsField("Height", QVariant.Double),
                QgsField("Azimuth", QVariant.Int),
                QgsField("DownTilt", QVariant.Int),
                QgsField("BeamWidth", QVariant.Int),
                QgsField(u"信息来源", QVariant.String),
                QgsField(u"小区半径（单位：米）", QVariant.Int),
                QgsField("CarrierPower", QVariant.Int),
                QgsField("Handover", QVariant.String),
                QgsField(u"站型", QVariant.String),
                QgsField("FN1", QVariant.Int),
                QgsField(u"载频数", QVariant.Int),
                QgsField("S-UARFCN1", QVariant.Int),
                QgsField("S-UARFCN2", QVariant.Int),
                QgsField("S-UARFCN3", QVariant.Int),
                QgsField("S-UARFCN4", QVariant.Int),
                QgsField("S-UARFCN5", QVariant.Int),
                QgsField("PCCPCHPower", QVariant.Double),
                QgsField("DwPCHPower", QVariant.Double),
                QgsField("FPACHPower", QVariant.Double),
                QgsField("N1", QVariant.Int),
                QgsField("N2", QVariant.Int),
                QgsField("N3", QVariant.Int),
                QgsField("N4", QVariant.Int),
                QgsField("N5", QVariant.Int),
                QgsField("N6", QVariant.Int),
                QgsField("N7", QVariant.Int),
                QgsField("N8", QVariant.Int),
                QgsField("N9", QVariant.Int),
                QgsField("N10", QVariant.Int),
                QgsField("N11", QVariant.Int),
                QgsField("N12", QVariant.Int),
                QgsField("N13", QVariant.Int),
                QgsField("N14", QVariant.Int),
                QgsField("N15", QVariant.Int),
                QgsField("N16", QVariant.Int),
                QgsField("N17", QVariant.Int),
                QgsField("N18", QVariant.Int),
                QgsField("N19", QVariant.Int),
                QgsField("N20", QVariant.Int),
                QgsField("N21", QVariant.Int),
                QgsField("N22", QVariant.Int),
                QgsField("N23", QVariant.Int),
                QgsField("N24", QVariant.Int),
                QgsField("N25", QVariant.Int),
                QgsField("N26", QVariant.Int),
                QgsField("N27", QVariant.Int),
                QgsField("N28", QVariant.Int),
                QgsField("N29", QVariant.Int),
                QgsField("N30", QVariant.Int),
                QgsField("N31", QVariant.Int),
                QgsField("N32", QVariant.Int),
                QgsField("Zone", QVariant.String),
                QgsField(u"高速公路覆盖", QVariant.String),
                QgsField(u"站点所属片区", QVariant.String),
                QgsField(u"设备厂家", QVariant.String),
                QgsField(u"类型", QVariant.String),
                QgsField(u"站点类型", QVariant.String),
                QgsField(u"H载波数", QVariant.Int),
                QgsField(u"G网格分区", QVariant.String),
                QgsField(u"Mod3", QVariant.String),
            ]
            return attrs
        elif fileType == '2G':
            attrs = [
                QgsField("CELL_NAME", QVariant.String),
                QgsField("BS_NO", QVariant.String),
                QgsField("CI", QVariant.Int),
                QgsField("ARFCN", QVariant.Int),
                QgsField("BSIC", QVariant.Int),
                QgsField("BEARING", QVariant.Int),
                QgsField("LAC", QVariant.Int),
                QgsField("NON_BCCH", QVariant.String),
                QgsField("DOWNTILT", QVariant.Int),
                QgsField("MAX_TX_BTS", QVariant.String),
                QgsField("ANT_HEIGH", QVariant.Int),
                QgsField("MAX_TX_MS", QVariant.String),
                QgsField("ANT_GAIN", QVariant.String),
                QgsField("ANT_TYPE", QVariant.String),
                QgsField("TIME", QVariant.String),
                QgsField("LON", QVariant.Double),
                QgsField("LAT", QVariant.Double),
                QgsField("BASETYPE", QVariant.Int),
                QgsField("LENGTH", QVariant.Int),
            ]
            for i in range(1, 49):
                attrs.append( QgsField("NCELL%d"%(i), QVariant.String))
            attrs.append( QgsField('Mod3', QVariant.Int))
            return attrs
        elif fileType == '2GFreqSearch':
            attrs = [
                QgsField("CELL_NAME", QVariant.String),
                QgsField("BS_NO", QVariant.String),
                QgsField("CI", QVariant.Int),
                QgsField("ARFCN", QVariant.Int),
                QgsField("BSIC", QVariant.Int),
                QgsField("BEARING", QVariant.Int),
                QgsField("LAC", QVariant.Int),
                QgsField("NON_BCCH", QVariant.String),
                QgsField("DOWNTILT", QVariant.Int),
                QgsField("MAX_TX_BTS", QVariant.String),
                QgsField("ANT_HEIGH", QVariant.Int),
                QgsField("MAX_TX_MS", QVariant.String),
                QgsField("ANT_GAIN", QVariant.String),
                QgsField("ANT_TYPE", QVariant.String),
                QgsField("TIME", QVariant.String),
                QgsField("LON", QVariant.Double),
                QgsField("LAT", QVariant.Double),
                QgsField("BASETYPE", QVariant.Int),
                QgsField("LENGTH", QVariant.Int),
            ]
            for i in range(1, 49):
                attrs.append( QgsField("NCELL%d"%(i), QVariant.String))
            attrs.append( QgsField('Condition', QVariant.Int))
            return attrs

    def saveEPSGChange(self):
        inputCRS = self.dlg.inputCRS.text().replace(" ", "")
        newString = ''
        basepath = os.path.dirname(os.path.realpath(__file__))
        settingsFile = os.path.join(basepath, 'settings.ini')
        initCRS = open(settingsFile, 'w')
        if self.storedCRS[1] != self.dlg.inputCRS.text().replace(" ", ""):
            newString += "EPSG=" + inputCRS + "\n"
        else:
            newString += "EPSG=" + self.storedCRS[1] + "\n"
        if len(self.filename) == 0:
            self.filename = self.storedLastFilePathLine[1]
        if self.storedLastFilePathLine[1] != self.filename[0: self.filename.rindex("/")+1]:
            newString += "LastFilePath="+self.filename[0: self.filename.rindex("/")+1]
        else:
            newString += "LastFilePath=" + self.storedLastFilePathLine[1]
        initCRS.write(newString.encode('utf-8'))
        initCRS.close()

