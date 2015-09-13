import sys
import random
import uuid
from PySide import QtGui, QtCore


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

		fileMenu = self.menuBar().addMenu("File")
		fileMenu.addAction(openImageAct)

		viewMenu = self.menuBar().addMenu("View")
		viewMenu.addAction(fitInViewAct)

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

	def GraphicsCanvasViewMouseDidMove(self, mousePos):
		if not self.image:
			return
		
		px = int(mousePos.x())
		py = int(mousePos.y())
		if (px < 0 or py < 0) or (px > self.image.width() or py > self.image.height()):
			self.statusBar().showMessage('')
			return

		rgb = self.image.pixel(px, py)
		color = QtGui.QColor(rgb)
		r = color.red()
		g = color.green()
		b = color.blue()
		self.statusBar().showMessage('Color <%s %s %s> @ <%s>' % (r, g, b, mousePos))


class GraphicsCanvasViewDelegate(object):
	def GraphicsCanvasViewMouseDidMove(self, mousePos):
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


class ColorListWidget(QtGui.QWidget):

	def __init__(self, parent=None):
		super(ColorListWidget, self).__init__(parent=parent)

		self.colorDataList = ColorDataList()
		self.addExampleColors()

		self.initLayout()

	def initLayout(self):
		grid = QtGui.QGridLayout()
		r = 0

		for colorDataUUID in self.colorDataList.getAllUUIDs():
			
			colorData = self.colorDataList.getCopyOfColorDataByUUID(colorDataUUID)

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

			grid.addWidget(nameText, r, 0)
			grid.addWidget(codeText, r, 1)
			grid.addWidget(redLabel, r, 2)
			grid.addWidget(greenLabel, r, 3)
			grid.addWidget(blueLabel, r, 4)

			r += 1

		self.grid = grid
		self.setLayout(grid)

	def addExampleColors(self):
		for i in range(1, 30):
			colorName = 'name %s' % i
			colorCode = 'code %s' % i
			red = random.randint(0, 255)
			green = random.randint(0, 255)
			blue = random.randint(0, 255)
			self.colorDataList.addNewColorData(colorName, colorCode, red, green, blue)

	def nameTextChanged(self, text):
		colorData = self.sender().colorData

		print "Change color name: %s" % text
		colorData.colorName = text
		self.colorDataList.commitChange(colorData)

		debugColorData = self.colorDataList.getCopyOfColorDataByUUID(colorData.getUUID())
		print "After changed - %s" % debugColorData.getDebugString()
		del debugColorData

	def codeTextChanged(self, text):
		colorData = self.sender().colorData

		print "Change color code: %s" % text
		colorData.colorCode = text
		self.colorDataList.commitChange(colorData)

		debugColorData = self.colorDataList.getCopyOfColorDataByUUID(colorData.getUUID())
		print "After changed - %s" % debugColorData.getDebugString()
		del debugColorData


def main():
	app = QtGui.QApplication(sys.argv)
	QtGui.QApplication.addLibraryPath('./')
	mainWindow = MainWindow()
	sys.exit(app.exec_())


if __name__ == '__main__':
	main()



