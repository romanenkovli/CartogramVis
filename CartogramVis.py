__version__ = '0.1'

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
import numpy as np
import sys
import math
from matplotlib import cm
import matplotlib.colors as cl


class MyWidget(QtWidgets.QWidget):
    def __init__(self, items, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.items = items
        self.setWindowTitle("LoadVis")
        self.layout = QtWidgets.QVBoxLayout()
        self.graphicsView = pg.PlotWidget()
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.setAspectLocked(1)
        self.graphicsView.plotItem.hideAxis('bottom')
        self.graphicsView.plotItem.hideAxis('left')

        self.pushButton = QtWidgets.QPushButton()
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText("Draw")
        self.pushButton_2 = QtWidgets.QPushButton()
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_2.setText("Clear")

        self.layout.addWidget(self.graphicsView)
        self.layout.addWidget(self.pushButton)
        self.layout.addWidget(self.pushButton_2)
        self.setLayout(self.layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(int(1000 / 100))
        self.i = 0
        self.isclear = True

        self.pushButton.clicked.connect(lambda: self.draw())
        self.pushButton_2.clicked.connect(lambda: self.clear())

    def draw(self):
        self.graphicsView.show()
        self.isclear = False

    def clear(self):
        self.graphicsView.plotItem.clear()
        self.isclear = True

    def update(self):
        if not self.isclear:
            self.graphicsView.clear()
            self.graphicsView.plot()
            for item in self.items:
                item.value = np.random.random()
                k = item.value
                item(k)
                self.graphicsView.plotItem.addItem(item)
                self.poly_text = pg.TextItem(str(round(item.value, 2)), color=QtGui.QColor(0, 0, 0))
                self.poly_text.setAnchor((0.5, 0.5))
                self.poly_text.setPos(item.coord[0], item.coord[1])
                self.graphicsView.plotItem.addItem(self.poly_text)


class PolygonItem(pg.GraphicsObject):
    def __init__(self, center_coordinates, value, cma):
        pg.GraphicsObject.__init__(self)
        self.coord = center_coordinates
        self.value = value
        self.cm = cma
        self.coordinates = []
        self.getHexCoordinates()
        self.generatePicture()

    def __call__(self, value):
        self.value = value
        self.getHexCoordinates()
        self.generatePicture()
        colormap = cm.get_cmap("YlOrRd")
        norm = cl.Normalize(0.5, 1.5)
        self.cm = colormap(norm(self.value))

    def getHexCoordinates(self):
        size = 10.
        self.coordinates = [
            QtCore.QPointF(self.coord[0], self.coord[1] + size / math.sqrt(3.)),
            QtCore.QPointF(self.coord[0] + size / 2., self.coord[1] + size / 2. / math.sqrt(3.)),
            QtCore.QPointF(self.coord[0] + size / 2., self.coord[1] - size / 2. / math.sqrt(3.)),
            QtCore.QPointF(self.coord[0], self.coord[1] - size / math.sqrt(3.)),
            QtCore.QPointF(self.coord[0] - size / 2., self.coord[1] - size / 2. / math.sqrt(3.)),
            QtCore.QPointF(self.coord[0] - size / 2., self.coord[1] + size / 2. / math.sqrt(3.))
        ]

    def generatePicture(self):
        # pre-computing a QPicture object allows paint() to run much more quickly,
        # rather than re-drawing the shapes every time.
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        p.setPen(pg.mkPen('w', width=1))
        brush = pg.mkBrush(
            self.cm[0]*255, self.cm[1]*255, self.cm[2]*255, self.cm[3]*255,
        )
        p.setBrush(brush)
        p.drawPolygon(
            self.coordinates[0],
            self.coordinates[1],
            self.coordinates[2],
            self.coordinates[3],
            self.coordinates[4],
            self.coordinates[5]
        )

    def paint(self, p):
        p.drawPicture(0, 0, self.picture)
        # font = QtGui.QFont()
        # font.setFamily('Tahoma')
        # font.setPixelSize(2)
        # font.setPointSizeF(1.)
        # p.setFont(font)
        # p.rotate(10)
        # p.drawText(self.picture, QtCore.Qt.AlignmentFlag.AlignCenter, str(self.value))
        # p.drawText(self.picture, QtCore.Qt.AlignmentFlag.AlignCenter, str(self.value))
        # p.drawText(QtCore.QPoint(self.coord[0], self.coord[1]), str(self.value))
        # p.drawText(self.coord[0], self.coord[1], str(self.value))

    def boundingRect(self):
        # boundingRect _must_ indicate the entire area that will be drawn on
        # or else we will get artifacts and possibly crashing.
        # (in this case, QPicture does all the work of computing the bounding rect for us)
        return QtCore.QRectF(self.picture.boundingRect())


class SketchLoadingInfo:
    def __init__(self, input_file):
        self.input_file = input_file
        self.values = 0
        self.center_coordinates = 0
        self.get_hexagons_info()
        self.colors = []

    def get_hexagons_info(self, threshold=0.0, step=10., isvver=True):
        # reading data to visualize from file
        val = list(map(
            lambda v: [abs(float(va)) for va in v.split()],
            [v for v in (self.vver() if isvver else open(file=self.input_file).readlines())])
        )
        # array of coordinates of hexagons, [x,y]
        c = list(map(lambda j: [[step * (i - j / 2.), -(j - 1) * step * math.sqrt(3.) / 2.] for i in range(len(val))],
                     [j for j in range(len(val))]))
        # removing dots with not desirable data
        c = list(filter(lambda c: c != None,
                        map(lambda v, c: c if v != threshold else None, [v for va in val for v in va],
                            [c for cs in c for c in cs])))
        # same but for value array
        val = list(filter(lambda v: v != threshold, [v for va in val for v in va]))

        self.center_coordinates = c
        self.values = val

        # Get the colormap
        colormap = cm.get_cmap("YlOrRd")
        norm = cl.Normalize(0.5, 1.5)
        for val in self.values:
            self.colors.append(colormap(norm(val)))

        self.cm = colormap

    def vver(self):
        v = open(file=self.input_file).readlines()
        v[0] = '0 ' * 2 + v[0] + '0 ' * 8
        v[1] = '0 ' + v[1] + '0 ' * 6
        v[2] = '0 ' + v[2] + '0 ' * 5
        v[3] = '0 ' + v[3] + '0 ' * 4
        v[4] = '0 ' + v[4] + '0 ' * 3
        v[5] = '0 ' + v[5] + '0 ' * 2
        v[6] = '0 ' + v[6] + '0 '
        v[7] = '0 ' * 2 + v[7] + '0 '
        v[8] = '0 ' * 2 + v[8]
        v[9] = '0 ' * 3 + v[9]
        v[10] = '0 ' * 4 + v[10]
        v[11] = '0 ' * 5 + v[11]
        v[12] = '0 ' * 6 + v[12]
        v[13] = '0 ' * 7 + v[13]
        v[14] = '0 ' * 9 + v[14] + '0 '
        v.append('0 ' * 16)
        return v


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    core_loading = SketchLoadingInfo("SKETCH_pow.lst")
    hexagons = []

    for i in range(len(core_loading.center_coordinates)):
        center_coordinates = core_loading.center_coordinates[i]
        value = core_loading.values[i]
        cma = core_loading.colors[i]
        hexagons.append(PolygonItem(center_coordinates, value, cma))

    window = MyWidget(hexagons)
    window.show()
    sys.exit(app.exec_())
