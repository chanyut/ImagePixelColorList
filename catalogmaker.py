import sys
import random
import uuid
from PySide import QtGui, QtCore

import media


class MainWindow(QtGui.QMainWindow):
	
	def __init__(self):
		super(MainWindow, self).__init__()

		self.canvasScene = None
		self.canvasView = None
		self.image = None
		self.imagePixmap = None
		self.imagePixmapGraphicsItem = None
		self.colorTableWidget = None

		self.initLayout()
		self.show()

	def initLayout(self):
		self.statusBar().showMessage('Ready')
		self.setGeometry(0, 0, 1024, 768)
		self.setWindowTitle('Catalog Maker')

		# Central widget
		canvasScene = QtGui.QGraphicsScene()
		canvasView = GraphicsCanvasView(canvasScene)
		canvasView.delegate = self
		self.setCentralWidget(canvasView)
		self.canvasScene = canvasScene
		self.canvasView = canvasView;

		# Right dock widget
		dock = QtGui.QDockWidget('Color List', self)
		dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
		colorTableWidget = ColorTableWidget()
		dock.setWidget(colorTableWidget)
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
		self.colorTableWidget = colorTableWidget

		openImageAct = QtGui.QAction('Open image', self)
		openImageAct.setStatusTip('Open image, and place into Canvas.')
		openImageAct.triggered.connect(self.openImage)

		fitInViewAct = QtGui.QAction('Fit in view', self)
		fitInViewAct.setStatusTip('Resize an image fit in Canvas view')
		fitInViewAct.triggered.connect(self.fitInView)

		reloadColorListAct = QtGui.QAction('Reload', self)
		reloadColorListAct.setStatusTip('Reload Color table')
		reloadColorListAct.triggered.connect(self.reloadColorList)

		loadFromCSVAct = QtGui.QAction('Load from CSV', self)
		loadFromCSVAct.setStatusTip('Load data from CSV')
		loadFromCSVAct.triggered.connect(self.loadFromCSV)

		exportAsCSVAct = QtGui.QAction('Export as CSV', self)
		exportAsCSVAct.setStatusTip('Export as CSV')
		exportAsCSVAct.triggered.connect(self.exportAsCSV)

		fileMenu = self.menuBar().addMenu('File')
		fileMenu.addAction(openImageAct)
		fileMenu.addAction(loadFromCSVAct)
		fileMenu.addAction(exportAsCSVAct)

		viewMenu = self.menuBar().addMenu('View')
		viewMenu.addAction(fitInViewAct)
		viewMenu.addAction(reloadColorListAct)

	def openImage(self):
		fileName,_ = QtGui.QFileDialog.getOpenFileName(self, 'Open Image', QtCore.QDir.currentPath(), 'Image Files (*.png *.jpg *.bmp)')
		self.imagePixmap = QtGui.QPixmap(fileName)
		self.image = self.imagePixmap.toImage()
		self.imagePixmapGraphicsItem = QtGui.QGraphicsPixmapItem(self.imagePixmap)
		self.canvasScene.addItem(self.imagePixmapGraphicsItem)
		self.canvasView.fitInView(self.imagePixmapGraphicsItem, QtCore.Qt.KeepAspectRatio)

	def fitInView(self):
		if self.canvasView == None or self.imagePixmapGraphicsItem == None:
			return
		self.canvasView.fitInView(self.imagePixmapGraphicsItem, QtCore.Qt.KeepAspectRatio)

	def reloadColorList(self):
		self.colorTableWidget.reload()

	def loadFromCSV(self):
		fileName,_ = QtGui.QFileDialog.getOpenFileName(self, 'Load CSV', QtCore.QDir.currentPath(), 'CSV Files (*.csv)')
		self.colorTableWidget.loadFromCSV(fileName)

	def exportAsCSV(self):
		format = 'csv'
		initialPath = QtCore.QDir.currentPath() + "/colorDataExport." + format
		fileName, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save As', initialPath, '%s Files (*.%s);;All Files (*)' % (format.upper(), format))
		
		if fileName:
			output = self.colorTableWidget.exportAsCSV()
			with open(fileName, 'w') as f:
				f.write(output)

	"""
	return QColor
	"""
	def _getPixelColorAtPoint(self, x, y):
		rgb = self.image.pixel(x, y)
		color = QtGui.QColor(rgb)
		return color		

	def GraphicsCanvasViewMouseDidMove(self, mousePos):
		if not self.image:
			return
		
		px = int(mousePos.x())
		py = int(mousePos.y())
		if (px < 0 or py < 0) or (px > self.image.width() or py > self.image.height()):
			self.statusBar().showMessage('')
			return

		color = self._getPixelColorAtPoint(px, py)
		r = color.red()
		g = color.green()
		b = color.blue()
		self.statusBar().showMessage('Color <%s %s %s> @ <%s>' % (r, g, b, mousePos))

	def GraphicsCanvasViewMouseDidPress(self, mousePos):
		if not self.image:
			return
		
		px = int(mousePos.x())
		py = int(mousePos.y())
		if (px < 0 or py < 0) or (px > self.image.width() or py > self.image.height()):
			self.statusBar().showMessage('')
			return

		color = self._getPixelColorAtPoint(px, py)
		r = color.red()
		g = color.green()
		b = color.blue()

		print 'Add new marker at %s which color is <%s %s %s>' % (mousePos, r, g, b)
		self.colorTableWidget.addNewColorData('', '', color)
		self.colorTableWidget.selectAndEditLastRowAtColumn(ColorTableWidget.COLUMN_COLOR_NAME)


class GraphicsCanvasViewDelegate(object):
	def GraphicsCanvasViewMouseDidMove(self, mousePos):
		pass
	def GraphicsCanvasViewMouseDidPress(self, mousePos):
		pass


class GraphicsCanvasView(QtGui.QGraphicsView):
	def __init__(self, graphicsScene, parent=None):
		super(GraphicsCanvasView, self).__init__(graphicsScene, parent=parent)
		self.setMouseTracking(True)
		self.setInteractive(True)
		self.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)
		self.onMouseMoveOnImage = None
		self.delegate = None

	def mouseMoveEvent(self, mouseEvent):
		pos = mouseEvent.pos()
		scenePos = self.mapToScene(pos)

		if self.delegate:
			self.delegate.GraphicsCanvasViewMouseDidMove(scenePos)
	
		super(GraphicsCanvasView, self).mouseMoveEvent(mouseEvent)

	def mousePressEvent(self, mouseEvent):
		pos = mouseEvent.pos()
		scenePos = self.mapToScene(pos)

		if mouseEvent.button() == QtCore.Qt.RightButton:
			if self.delegate:
				self.delegate.GraphicsCanvasViewMouseDidPress(scenePos)
		else:
			super(GraphicsCanvasView, self).mousePressEvent(mouseEvent)
	
	def wheelEvent(self, wheelEvent):
		"""
		Credit: http://stackoverflow.com/questions/19113532/qgraphicsview-zooming-in-and-out-under-mouse-position-using-mouse-wheel
		Answer from User: Rengel
		"""
		zoomInFactor = 1.25
		zoomOutFactor = 1 / zoomInFactor

		# Save the scene pos
		oldPos = self.mapToScene(wheelEvent.pos())

		# Zoom
		if wheelEvent.delta() > 0:
		    zoomFactor = zoomInFactor
		else:
		    zoomFactor = zoomOutFactor
		self.scale(zoomFactor, zoomFactor)

		# Get the new position
		newPos = self.mapToScene(wheelEvent.pos())

		# Move scene to old position
		delta = newPos - oldPos
		self.translate(delta.x(), delta.y())


class ColorData(object):

	def __init__(self, newUUID):
		super(ColorData, self).__init__()

		self._uuid = newUUID
		self.colorCode = ''
		self.colorName = ''
		self.red = 0
		self.green = 0
		self.blue = 0

	def getDebugString(self):
		return "%s %s - <%s %s %s>" % (self.colorCode, self.colorName, self.red, self.green, self.blue)

	def getUUID(self):
		return self._uuid

	def clone(self):
		newColorData = ColorData(self._uuid)
		newColorData.colorName = self.colorName
		newColorData.colorCode = self.colorCode
		newColorData.red = self.red
		newColorData.green = self.green
		newColorData.blue = self.blue
		return newColorData

	def copyFrom(self, otherColorData):
		self.colorName = otherColorData.colorName
		self.colorCode = otherColorData.colorCode
		self.red = otherColorData.red
		self.green = otherColorData.green
		self.blue = otherColorData.blue


class ColorDataList(object):

	def __init__(self):
		super(ColorDataList, self).__init__()
		self._internalList = []

	def addNewColorData(self, name, code, red, green, blue, colorDataUUID=None):
		if not colorDataUUID:
			colorDataUUID = uuid.uuid1()

		newColorData = ColorData(colorDataUUID)
		newColorData.colorName = name
		newColorData.colorCode = code
		newColorData.red = red
		newColorData.green = green
		newColorData.blue = blue
		self._internalList.append(newColorData)
		return newColorData.getUUID()

	def getCopyOfColorDataByUUID(self, findUUID):
		for c in self._internalList:
			if c.getUUID() == findUUID:
				return c.clone()
		return None

	def removeColorDataByUUID(self, removeUUID):
		for c in self._internalList:
			if c.getUUID() == removeUUID:
				self._internalList.remove(c)
				return True
		return False

	def commitChange(self, colorData):
		for c in self._internalList:
			if c.getUUID() == colorData.getUUID():
				c.copyFrom(colorData)
				return True
		return False

	def clearAll(self):
		del self._internalList
		self._internalList = []
		
	def numberOfTotalColors(self):
		return len(self._internalList)

	def getAllUUIDs(self):
		for c in self._internalList:
			yield c.getUUID()

	def loadFromCSVContent(self, content, delimeter=';'):
		self.clearAll()
		lines = content.split('\n')
		for line in lines:
			c = line.split(delimeter)
			if len(c) != 6:
				continue

			colorUUID = uuid.UUID(c[0])
			name = c[1]
			code = c[2]
			red = int(c[3])
			green = int(c[4])
			blue = int(c[5])
			self.addNewColorData(name, code, red, green, blue, colorDataUUID=colorUUID)

	def exportAsCSV(self, delimeter=';'):
		outputString = ''
		for colorData in self._internalList:
			outputString += str(colorData.getUUID()) + delimeter
			outputString += colorData.colorName + delimeter
			outputString += colorData.colorCode + delimeter
			outputString += str(colorData.red) + delimeter
			outputString += str(colorData.green) + delimeter
			outputString += str(colorData.blue) + '\n'
		return outputString


class ColorThumbnail(QtGui.QWidget):
	def __init__(self, color, parent=None):
		super(ColorThumbnail, self).__init__(parent)
		self.color = color

	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		painter.fillRect(self.rect(), self.color)
		painter.drawRect(self.rect())


class ColorTableWidget(QtGui.QTableWidget):

	COLUMN_COLOR_THUMBNAIL = 0
	COLUMN_COLOR_NAME = 1
	COLUMN_COLOR_CODE = 2
	COLUMN_COLOR_RED = 3
	COLUMN_COLOR_GREEN = 4
	COLUMN_COLOR_BLUE = 5

	def __init__(self, parent=None):
		super(ColorTableWidget, self).__init__(0, 6, parent)
		
		self._colorDataList = ColorDataList()

		self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
		self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
		self.setHorizontalHeaderLabels(('', 'Name', 'Code', 'R', 'G', 'B'))
		self.horizontalHeader().setResizeMode(ColorTableWidget.COLUMN_COLOR_NAME, QtGui.QHeaderView.Stretch)
		self.horizontalHeader().setResizeMode(ColorTableWidget.COLUMN_COLOR_CODE, QtGui.QHeaderView.Stretch)
		self.horizontalHeader().resizeSection(ColorTableWidget.COLUMN_COLOR_THUMBNAIL, 26)
		self.horizontalHeader().resizeSection(ColorTableWidget.COLUMN_COLOR_RED, 40)
		self.horizontalHeader().resizeSection(ColorTableWidget.COLUMN_COLOR_GREEN, 40)
		self.horizontalHeader().resizeSection(ColorTableWidget.COLUMN_COLOR_BLUE, 40)
		
		self.verticalHeader().hide()
		self.setShowGrid(True)

		self.cellActivated.connect(self.onTableCellActivated)
		self.cellChanged.connect(self.onTableCellChanged)

	def onTableCellActivated(self, row, column):
		item = self.item(row, ColorTableWidget.COLUMN_COLOR_NAME)
		if not item:
			return
		if not hasattr(item, 'colorDataUUID'):
			return

		colorUUID = item.colorDataUUID
		colorData = self._colorDataList.getCopyOfColorDataByUUID(colorUUID)
		colorCode = colorData.colorCode
		print 'cell activate at row: %s col: %s => %s [%s]' % (row, column, colorData.colorCode, colorUUID)
		
	def onTableCellChanged(self, row, column):
		if column in [ColorTableWidget.COLUMN_COLOR_NAME, ColorTableWidget.COLUMN_COLOR_CODE]:
			item = self.item(row, column)
			if not hasattr(item, 'colorDataUUID'):
				return

			colorUUID = item.colorDataUUID
			colorData = self._colorDataList.getCopyOfColorDataByUUID(colorUUID)
			newValue = item.text()
			
			if column == ColorTableWidget.COLUMN_COLOR_NAME:
				colorData.colorName = newValue
			elif column == ColorTableWidget.COLUMN_COLOR_CODE:
				colorData.colorCode = newValue

			self._colorDataList.commitChange(colorData)

	def _addNewBlankRow(self):
		colorThumbnail = ColorThumbnail(QtGui.QColor(QtCore.Qt.white), parent=self)
		colorThumbnail.setFixedSize(24, 24)

		colorNameItem = QtGui.QTableWidgetItem('')
		colorNameItem.setFlags(colorNameItem.flags() | QtCore.Qt.ItemIsEditable)

		colorCodeItem = QtGui.QTableWidgetItem('')
		colorCodeItem.setFlags(colorNameItem.flags() | QtCore.Qt.ItemIsEditable)

		colorRedItem = QtGui.QTableWidgetItem('0')
		colorRedItem.setFlags(colorNameItem.flags() ^ QtCore.Qt.ItemIsEditable)

		colorGreenItem = QtGui.QTableWidgetItem('0')
		colorGreenItem.setFlags(colorNameItem.flags() ^ QtCore.Qt.ItemIsEditable)

		colorBlueItem = QtGui.QTableWidgetItem('0')
		colorBlueItem.setFlags(colorNameItem.flags() ^ QtCore.Qt.ItemIsEditable)

		row = self.rowCount()
		self.insertRow(row)
		self.setCellWidget(row, ColorTableWidget.COLUMN_COLOR_THUMBNAIL, colorThumbnail)
		self.setItem(row, ColorTableWidget.COLUMN_COLOR_NAME, colorNameItem)
		self.setItem(row, ColorTableWidget.COLUMN_COLOR_CODE, colorCodeItem)
		self.setItem(row, ColorTableWidget.COLUMN_COLOR_RED, colorRedItem)
		self.setItem(row, ColorTableWidget.COLUMN_COLOR_GREEN, colorGreenItem)
		self.setItem(row, ColorTableWidget.COLUMN_COLOR_BLUE, colorBlueItem)

	def _setColorDataAt(self, row, colorData):
		colorDataUUID = colorData.getUUID()
		colorName = colorData.colorName
		colorCode = colorData.colorCode
		red = colorData.red
		green = colorData.green
		blue = colorData.blue

		colorThumbnail = self.cellWidget(row, ColorTableWidget.COLUMN_COLOR_THUMBNAIL)
		colorThumbnail.color = QtGui.QColor(red, green, blue)

		colorNameItem = self.item(row, ColorTableWidget.COLUMN_COLOR_NAME)
		colorNameItem.setText(colorName)
		colorNameItem.colorDataUUID = colorDataUUID
		
		colorCodeItem = self.item(row, ColorTableWidget.COLUMN_COLOR_CODE)
		colorCodeItem.setText(colorCode)
		colorCodeItem.colorDataUUID = colorDataUUID

		colorRedItem = self.item(row, ColorTableWidget.COLUMN_COLOR_RED)
		colorRedItem.setText(str(red))

		colorGreenItem = self.item(row, ColorTableWidget.COLUMN_COLOR_GREEN)
		colorGreenItem.setText(str(green))

		colorBlueItem = self.item(row, ColorTableWidget.COLUMN_COLOR_BLUE)
		colorBlueItem.setText(str(blue))

	def addNewColorData(self, colorName, colorCode, colorAsQColor):
		r = colorAsQColor.red()
		g = colorAsQColor.green()
		b = colorAsQColor.blue()
		colorDataUUID = self._colorDataList.addNewColorData(colorName, colorCode, r, g, b)
		colorData = self._colorDataList.getCopyOfColorDataByUUID(colorDataUUID)

		self._addNewBlankRow()
		row = self.rowCount()
		row -= 1
		self._setColorDataAt(row, colorData)

	def selectAndEditLastRowAtColumn(self, column):
		row = self.rowCount() - 1
		item = self.item(row, column)
		self.setCurrentCell(row, column)
		self.editItem(item)

	def reload(self):
		numberOfTotalColors = self._colorDataList.numberOfTotalColors()

		while self.rowCount() > numberOfTotalColors:
			self.removeRow(0)

		while self.rowCount() < numberOfTotalColors:
			self._addNewBlankRow()

		row = 0
		for colorDataUUID in self._colorDataList.getAllUUIDs():
			colorData = self._colorDataList.getCopyOfColorDataByUUID(colorDataUUID)
			self._setColorDataAt(row, colorData)
			row += 1

	def exportAsCSV(self, delimeter=';'):
		return self._colorDataList.exportAsCSV(delimeter)

	def loadFromCSV(self, fileName):
		content = None
		with open(fileName) as f:
			content = f.read()
		if not content:
			return

		self._colorDataList.loadFromCSVContent(content)
		self.reload()


def main():
	app = QtGui.QApplication(sys.argv)
	QtGui.QApplication.addLibraryPath('./')
	mainWindow = MainWindow()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()



