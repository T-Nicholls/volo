from PyQt5.QtWidgets import QApplication, QMainWindow, QGroupBox, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush
from PyQt5.QtCore import Qt, QRect, QMargins

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import sys
import at
import at.plot
import numpy
from collections import OrderedDict
import atip.ease as e
import math
import time


class Window(QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        lattice = e.loader()
        self.lattice = e.get_sim_ring(lattice)
        self._atsim = e.get_atsim(lattice)
        self.s_selection = None
        self.total_len = sum([elem.Length for elem in self.lattice])
        self.n = 1
        if self.n is not None:
            superperiod_len = self.total_len / 6.0
            superperiod_bounds = superperiod_len * numpy.array(range(7))
            self.lattice.s_range = superperiod_bounds[self.n-1:self.n+1]
            self.total_len = self.lattice.s_range[1] - self.lattice.s_range[0]
        self.initUI()

    def initUI(self):
        #print(self.frameGeometry())
        self.setGeometry(0, 0, 1500, 800)
        # initialise layouts
        layout = QHBoxLayout()
        layout.setSpacing(20)
        #layout.setStretch(0, 0)
        self.left_side = QVBoxLayout()
        self.left_side.setAlignment(Qt.AlignLeft)

        # create graph
        graph = QHBoxLayout()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.graph_onclick)
        self.plot()
        #self.canvas.resize(1000, 480)
        self.canvas.setMinimumWidth(1000)
        self.canvas.setMinimumHeight(480)
        self.canvas.setMaximumHeight(480)
        self.graph_width = 1000
        #self.canvas._dpi_ratio = 2
        self.figure.set_tight_layout({"pad": 0.5, "w_pad": 0, "h_pad": 0})
        graph.addWidget(self.canvas)
        self.left_side.addLayout(graph)
        # data3.setToolTip("m")
        # border-bottom-width:1px;border-bottom-style:solid; border-radius:0px

        # create lattice representation bar
        #wrapper = QWidget(self)
        #wrapper.setMinimumSize(1000, 120)
        #repr_box = QHBoxLayout(wrapper)
        #repr_box.setSpacing(0)
        self.container = QWidget(self)
        #self.container.setStyleSheet("background-color:white")
        #self.container.setMinimumSize(880, 120)
        self.lat_disp = QHBoxLayout(self.container)
        self.lat_disp.setSpacing(0)
        #self.lat_disp.setAlignment(Qt.AlignHCenter)
        #self.lat_disp.setContentsMargins(QMargins(0, 0, 0, 0))
        #self.lat_disp.setStretch(0, 0)
        # add first spacer and offset
        lat_repr, space = self.create_lat_repr(1500)
        if space > 0:
            self.lat_disp.addSpacing(space)
        # add element lines
        for elem_repr in lat_repr:
                self.lat_disp.addWidget(elem_repr)
        # add end spacer
        if space > 0:
            self.lat_disp.addSpacing(space)
        #for i in range(self.lat_disp.count()):
            #print(self.lat_disp.stretch(i))
        #repr_box.addStretch()
        #repr_box.addWidget(self.container)
        #repr_box.addStretch()
        #left_side.addWidget(self.container)
        #left_side.addLayout(self.lat_disp)

        # create elem editing boxes to drop to
        bottom = QHBoxLayout()
        box1, data1 = self.create_edit_box()
        bottom.addWidget(box1)
        box2, data2 = self.create_edit_box()
        bottom.addWidget(box2)
        box3, data3 = self.create_edit_box()
        bottom.addWidget(box3)
        box4, data4 = self.create_edit_box()
        bottom.addWidget(box4)
        self.left_side.addLayout(bottom)
        self.left_side.addStretch()

        # all components now set add to main layout
        layout.addLayout(self.left_side)

        # create lattice and element data sidebar
        sidebar = QGridLayout()
        sidebar.setSpacing(10)
        self.lattice_data_widgets = {}
        if self.n is None:
            title = QLabel("Global Lattice Parameters:")
        else:
            title = QLabel("Global Super Period Parameters:")
        title.setMaximumWidth(220)
        title.setMinimumWidth(220)
        title.setStyleSheet("font-weight:bold; text-decoration:underline")
        sidebar.addWidget(title, 0, 0)
        spacer = QLabel("")
        spacer.setMaximumWidth(220)
        spacer.setMinimumWidth(220)
        sidebar.addWidget(spacer, 0, 1)
        row_count = 1
        for field, value in self.get_lattice_data().items():
            val_str = self.stringify(value)
            sidebar.addWidget(QLabel("{0}: ".format(field)), row_count, 0)
            lab = QLabel(val_str)
            sidebar.addWidget(lab, row_count, 1)
            self.lattice_data_widgets[field] = lab
            row_count += 1
        self.element_data_widgets = {}
        title = QLabel("Selected Element Parameters:")
        title.setStyleSheet("font-weight:bold; text-decoration:underline")
        sidebar.addWidget(title, row_count, 0)
        row_count += 1
        for field, value in self.get_element_data(0).items():
            sidebar.addWidget(QLabel("{0}: ".format(field)), row_count, 0)
            lab = QLabel("N/A")
            sidebar.addWidget(lab, row_count, 1)
            self.element_data_widgets[field] = lab
            row_count += 1
        layout.addLayout(sidebar)

        # set layout
        wid = QWidget(self)
        wid.setLayout(layout)
        self.setCentralWidget(wid)
        #self.setStyleSheet("background-color:white")
        self.show()

    def create_lat_repr(self, repr_len=None):
        # create element representations
        if repr_len is None:
            repr_len = int(self.axl.get_window_extent().width)
        if repr_len < 880:
            repr_len = 880
        ratio = repr_len / self.total_len
        total_width = 0
        lat_repr = []
        for elem in self.lattice[self.lattice.i_range]:
            width = elem.Length * ratio
            if width >= 1:
                width = int(width)
            else:
                width = math.ceil(width)
            if width != 0:
                total_width += width
                if isinstance(elem, at.elements.Drift):
                    colour = Qt.gray
                elif isinstance(elem, at.elements.Dipole):
                    colour = Qt.green
                elif isinstance(elem, at.elements.Quadrupole):
                    colour = Qt.red
                elif isinstance(elem, at.elements.Sextupole):
                    colour = Qt.yellow
                else:
                    #print(type(elem))
                    colour = Qt.blue
                elem_repr = element_repr(width, colour)
                elem_repr.resize(width, 100)
                #elem_repr.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                #elem_repr.setStyleSheet("background-color:grey")
                lat_repr.append(elem_repr)
        # calculate spacers
        space = (self.frameGeometry().width() - 5180 - total_width) / 2
        #print(self.frameGeometry().width(), repr_len, total_width, space)
        space = 100
        return lat_repr, math.ceil(space)

    def create_edit_box(self):
        data_labels = {}
        box = QGroupBox()
        box.setMaximumSize(200, 200)
        grid = QGridLayout()
        #grid.setColumnStretch(0, 0)
        #grid.setRowStretch(0, 0)
        data_labels["Index"] = QLabel("N/A")
        grid.addWidget(QLabel("Index"), 0, 0)
        grid.addWidget(data_labels["Index"], 0, 1)
        data_labels["Type"] = QLabel("N/A")
        grid.addWidget(QLabel("Type"), 1, 0)
        grid.addWidget(data_labels["Type"], 1, 1)
        data_labels["Length"] = QLabel("N/A")
        grid.addWidget(QLabel("Length"), 2, 0)
        grid.addWidget(data_labels["Length"], 2, 1)
        data_labels["PassMethod"] = QLabel("N/A")
        grid.addWidget(data_labels["PassMethod"], 3, 1)
        grid.addWidget(QLabel("PassMethod"), 3, 0)
        data_labels["SetPoint"] = (QLabel("Set Point Field"), QLabel("N/A"))
        grid.addWidget(data_labels["SetPoint"][1], 5, 1)
        grid.addWidget(data_labels["SetPoint"][0], 5, 0)
        box.setLayout(grid)
        return box, data_labels

    def get_lattice_data(self):
        data_dict = OrderedDict()
        data_dict["Number of Elements"] = len(self.lattice.i_range)
        data_dict["Total Length"] = self.total_len
        data_dict["Cell Tune"] = [self._atsim.get_tune(0),
                                  self._atsim.get_tune(1)]
        data_dict["Linear Chromaticity"] = [self._atsim.get_chrom(0),
                                            self._atsim.get_chrom(1)]
        data_dict["Horizontal Emittance"] = self._atsim.get_emit(0) * 1e12
        data_dict["Linear Dispersion Action"] = 0.0
        data_dict["Momentum Spread"] = 0.0
        data_dict["Linear Momentum Compaction"] = self._atsim.get_mcf()
        data_dict["Energy Loss per Turn"] = self._atsim.get_energy_loss()
        data_dict["Damping Times"] = self._atsim.get_damping_times() * 1e3
        data_dict["Damping Partition Numbers"] = [0, 0, 0]
        data_dict["Total Bend Angle"] = self._atsim.get_total_bend_angle()
        data_dict["Total Absolute Bend Angle"] = self._atsim.get_total_absolute_bend_angle()
        return data_dict

    def get_element_data(self, selected_s_pos):
        data_dict = OrderedDict()
        all_s = self._atsim.get_s()
        index = int(numpy.where([s <= selected_s_pos for s in all_s])[0][-1])
        data_dict["Selected S Position"] = selected_s_pos
        data_dict["Element Index"] = index
        data_dict["Element Start S Position"] = all_s[index]
        data_dict["Element Length"] = self._atsim.get_at_element(index+1).Length
        data_dict["Horizontal Linear Dispersion"] = self._atsim.get_disp()[index, 0]
        data_dict["Beta Function"] = self._atsim.get_beta()[index]
        data_dict["Derivative of Beta Function"] = self._atsim.get_alpha()[index]
        data_dict["Normalized Phase Advance"] = self._atsim.get_mu()[index]/(2*numpy.pi)
        return data_dict

    def stringify(self, value):
        v = []
        if numpy.issubdtype(type(value), numpy.number):
            value = [value]
        for val in value:
            if isinstance(val, int):
                v.append("{0:d}".format(val))
            else:
                if val == 0:
                    v.append("0.0")
                elif abs(val) < 0.1:
                    v.append("{0:.5e}".format(val))
                else:
                    v.append("{0:.5f}".format(val))
        if len(v) == 1:
            return v[0]
        else:
            return "[" + ', '.join(v) + "]"

    def update_lattice_data(self):
        for field, value in self.get_lattice_data().items():
            val_str = self.stringify(value)
            self.lattice_data_widgets[field].setText(val_str)

    def update_element_data(self, s_pos):
        for field, value in self.get_element_data(s_pos).items():
            val_str = self.stringify(value)
            self.element_data_widgets[field].setText(val_str)

    def plot(self):
        self.lattice.radiation_off()
        self.figure.clear()
        self.axl = self.figure.add_subplot(111, xmargin=0, ymargin=0.025)
        self.axl.set_xlabel('s position [m]')
        self.axr = self.axl.twinx()
        self.axr.margins(0, 0.025)
        at.plot.plot_beta(self.lattice, axes=(self.axl, self.axr))
        self.canvas.draw()

    def graph_onclick(self, event):
        if event.xdata is not None:
            if self.s_selection is not None:
                self.s_selection.remove()
                for lab in self.element_data_widgets.values():
                    lab.setText("N/A")
            if event.button == 1:
                self.s_selection = self.axl.axvline(event.xdata, color="black",
                                                    linestyle='--', zorder=3)
                self.update_element_data(event.xdata)
            else:
                self.s_selection = None
            self.canvas.draw()
            self.resize_graph(True)
        """
        print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
              ('double' if event.dblclick else 'single', event.button,
               event.x, event.y, event.xdata, event.ydata))
        """

    def resize_graph(self, redraw=False):
        width = max([self.frameGeometry().width() - 500, 1000])
        if (int(width) != int(self.graph_width)) or redraw:
            #dpi = self.figure.dpi
            self.canvas.flush_events()
            #self.figure.set_size_inches(width/dpi, 480/dpi, forward=True)
            self.canvas.resize(width, 480)
            self.graph_width = width

    def resizeEvent(self, event):
        self.resize_graph()
        """
        for i in reversed(range(self.lat_disp.count())):
            widget = self.lat_disp.takeAt(i)
            #self.lat_disp.removeWidget(widget)
            if not isinstance(widget, QSpacerItem):
                widget.widget().close()
        lat_repr, space = self.create_lat_repr()
        # add first spacer and offset
        self.lat_disp.addSpacing(space)
        # add element lines
        for elem_repr in lat_repr:
                self.lat_disp.addWidget(elem_repr)
        # add end spacer
        self.lat_disp.addSpacing(space)
        """"""
        lat_repr, space = self.create_lat_repr()
        for i in range(self.lat_disp.count()-2):
            widget = self.lat_disp.takeAt(1)
            widget.widget().close()
            widget.widget().deleteLater()
        # put new elem representations in
        for elem_repr in reversed(lat_repr):
            self.lat_disp.insertWidget(1, elem_repr, 0)
        # update spacer elements
        self.lat_disp.itemAt(0).changeSize(space, 100)
        self.lat_disp.itemAt(self.lat_disp.count()-1).changeSize(space, 100)
        #print(self.lat_disp.itemAt(0))
        """
        super().resizeEvent(event)


class element_repr(QWidget):
    def __init__(self, width, colour):
        super().__init__()
        self.width = width
        self.colour = colour

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setPen(self.colour)
        qp.setBrush(self.colour)
        qp.drawRect(0, 0, self.width, 100)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())
