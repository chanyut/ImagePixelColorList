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
		self.colorListWidget = None

		self.initLayout()
		self.show()

	def initLayout(self):
		self.statusBar().showMessage('Ready')
		self.setGeometry(0, 0, 400, 400)
		self.setWindowTitle('Catalog Maker')

		# Central widget
		canvasScene = QtGui.QGraphicsScene()
		canvasView = GraphicsCanvasView(canvasScene)
		canvasView.delegate = self
		self.setCentralWidget(canvasView)
		self.canvasScene = canvasScene
		self.canvasView = canvasView;

		# Right dock widget
		dock = QtGui.QDockWidget("Color List", self)
		dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
		colorList = ColorListWidget(dock)
		scrollArea = QtGui.QScrollArea()
		scrollArea.setWidget(colorList)
		dock.setWidget(scrollArea)
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
		self.colorListWidget = colorList

		openImageAct = QtGui.QAction("Open image", self)
		openImageAct.setStatusTip("Open image, and place into Canvas.")
		openImageAct.triggered.connect(self.openImage)

		fitInViewAct = QtGui.QAction("Fit in view", self)
		fitInViewAct.setStatusTip("Resize an image fit in Canvas view")
		fitInViewAct.triggered.connect(self.fitInView)

		reloadColorListAct = QtGui.QAction("Reload", self)
		reloadColorListAct.setStatusTip("Reload Color table")
		reloadColorListAct.triggered.connect(self.reloadColorList)

		fileMenu = self.menuBar().addMenu("File")
		fileMenu.addAction(openImageAct)

		viewMenu = self.menuBar().addMenu("View")
		viewMenu.addAction(fitInViewAct)
		viewMenu.addAction(reloadColorListAct)

	def openImage(self):
		fileName = QtGui.QFileDialog.getOpenFileName(self, "Open Image", "~/Desktop", "Image Files (*.png *.jpg *.bmp)")
		self.imagePixmap = QtGui.QPixmap(fileName[0])
		self.image = self.imagePixmap.toImage()
		self.imagePixmapGraphicsItem = QtGui.QGraphicsPixmapItem(self.imagePixmap)
		self.canvasScene.addItem(self.imagePixmapGraphicsItem)
		self.canvasView.fitInView(self.imagePixmapGraphicsItem, QtCore.Qt.KeepAspectRatio)

	def fitInView(self):
		if self.canvasView == None or self.imagePixmapGraphicsItem == None:
			return
		self.canvasView.fitInView(self.imagePixmapGraphicsItem, QtCore.Qt.KeepAspectRatio)

	def reloadColorList(self):
		self.colorListWidget.reload()

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

		print "Add new marker at %s which color is <%s %s %s>" % (mousePos, r, g, b)
		self.colorListWidget.addNewColorData("", "", color)


class GraphicsCanvasViewDelegate(object):
	def GraphicsCanvasViewMouseDidMove(self, mousePos):
		pass
	def GraphicsCanvasViewMouseDidPress(self, mousePos):
		pass


class GraphicsCanvasView(QtGui.QGraphicsView):
	def __init__(self, graphicsScene, parent=None):
		super(GraphicsCanvasView, self).__init__(graphicsScene, parent=parent)
		self.setMouseTracking(True)
		self.onMouseMoveOnImage = None
		self.delegate = None

	def mouseMoveEvent(self, mouseEvent):
		pos = mouseEvent.pos()
		scenePos = self.mapToScene(pos)
		if self.delegate:
			self.delegate.GraphicsCanvasViewMouseDidMove(scenePos)

	def mousePressEvent(self, mouseEvent):
		pos = mouseEvent.pos()
		scenePos = self.mapToScene(pos)
		if self.delegate:
			self.delegate.GraphicsCanvasViewMouseDidPress(scenePos)


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

	def addNewColorData(self, name, code, red, green, blue):
		newColorData = ColorData(uuid.uuid1())
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

	def getAllUUIDs(self):
		for c in self._internalList:
			yield c.getUUID()


class ColorThumbnail(QtGui.QWidget):
	def __init__(self, color, parent=None):
		super(ColorThumbnail, self).__init__(parent)
		self.color = color

	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		painter.fillRect(self.rect(), self.color)
		painter.drawRect(self.rect())


class ColorListWidget(QtGui.QWidget):

	ENTRY_HEIGHT = 32

	def __init__(self, parent=None):
		super(ColorListWidget, self).__init__(parent=parent)

		self._colorDataList = ColorDataList()

		self.initLayout()
		# self.addExampleColors()
		self.reload()

	def initLayout(self):
		grid = QtGui.QGridLayout()
		self.grid = grid
		self.setLayout(grid)

	def reload(self):
		grid = self.grid

		while grid.count() > 0:
			layoutItem = grid.takeAt(0)
			widget = layoutItem.widget()
			widget.setParent(None)
			widget.deleteLater()

		for colorDataUUID in self._colorDataList.getAllUUIDs():
			colorData = self._colorDataList.getCopyOfColorDataByUUID(colorDataUUID)

			nameText = QtGui.QLineEdit()
			nameText.colorData = colorData
			nameText.setText(colorData.colorName)
			nameText.textChanged.connect(self.nameTextChanged)

			codeText = QtGui.QLineEdit()
			codeText.colorData = colorData
			codeText.setText(colorData.colorCode)
			codeText.textChanged.connect(self.codeTextChanged)

			redLabel = QtGui.QLabel()
			redLabel.colorData = colorData
			redLabel.setText(str(colorData.red))

			greenLabel = QtGui.QLabel()
			greenLabel.colorData = colorData
			greenLabel.setText(str(colorData.green))

			blueLabel = QtGui.QLabel()
			blueLabel.colorData = colorData
			blueLabel.setText(str(colorData.blue))

			color = QtGui.QColor(colorData.red, colorData.green, colorData.blue)
			colorThumbnail = ColorThumbnail(color, parent=self)
			colorThumbnail.setFixedSize(24, 24)

			r = grid.count()
			grid.addWidget(colorThumbnail, r, 0)
			grid.addWidget(nameText, r, 1)
			grid.addWidget(codeText, r, 2)
			grid.addWidget(redLabel, r, 3)
			grid.addWidget(greenLabel, r, 4)
			grid.addWidget(blueLabel, r, 5)

		self.resize(self.sizeHint())

	def sizeHint(self):
		size = QtCore.QSize(320, 10);
		numberOfRows = self.grid.rowCount()
		
		for r in range(0, numberOfRows):
			layoutItem = self.grid.itemAtPosition(r, 0)
			if not layoutItem:
				continue

			widget = layoutItem.widget()
			h = size.height()
			h += ColorListWidget.ENTRY_HEIGHT
			h += self.grid.spacing()
			size.setHeight(h)

		return size

	def addExampleColors(self):
		for i in range(1, 30):
			colorName = 'name %s' % i
			colorCode = 'code %s' % i
			red = random.randint(0, 255)
			green = random.randint(0, 255)
			blue = random.randint(0, 255)
			color = QtGui.QColor(red, green, blue)
			self.addNewColorData(colorName, colorCode, color)

	def nameTextChanged(self, text):
		colorData = self.sender().colorData

		print "Change color name: %s" % text
		colorData.colorName = text
		self._colorDataList.commitChange(colorData)

		debugColorData = self._colorDataList.getCopyOfColorDataByUUID(colorData.getUUID())
		print "After changed - %s" % debugColorData.getDebugString()
		del debugColorData

	def codeTextChanged(self, text):
		colorData = self.sender().colorData

		print "Change color code: %s" % text
		colorData.colorCode = text
		self._colorDataList.commitChange(colorData)

		debugColorData = self._colorDataList.getCopyOfColorDataByUUID(colorData.getUUID())
		print "After changed - %s" % debugColorData.getDebugString()
		del debugColorData

	def addNewColorData(self, colorName, colorCode, colorAsQColor):
		r = colorAsQColor.red()
		g = colorAsQColor.green()
		b = colorAsQColor.blue()
		self._colorDataList.addNewColorData(colorName, colorCode, r, g, b)
		self.reload()

	def paintEvent(self, paintEvent):
		pass


def main():
	app = QtGui.QApplication(sys.argv)
	QtGui.QApplication.addLibraryPath('./')
	mainWindow = MainWindow()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()



