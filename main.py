import sys
import base64
import requests
import json
import matplotlib.mathtext as math_text
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QApplication, QLineEdit, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtCore import Qt, QRect, QSize, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QFont, QPixmap, QScreen, QColor, QPen, QIcon


class Result(QWidget):
    def __init__(self, parent=None):
        super(Result, self).__init__(parent)
        self.capture = Capture(None)
        self.draw = Canvas(None)
        self.setAcceptDrops(True)
        self.setWindowIcon(QIcon("favicon.ico"))
        # region WindowSettings
        self.setFixedWidth(600)
        self.setWindowTitle("MathPix+")
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        # endregion
        # region Svg
        self.svg_container = QWidget()
        self.svg_container.setFixedSize(QSize(578, 200))
        self.svg = QSvgWidget(self.svg_container)
        # endregion
        # region Info Label
        self.label = QLabel()
        self.label.setFont(QFont("等线", 20))
        self.label.setMaximumHeight(30)
        self.label.setAlignment(Qt.AlignCenter)
        # endregion
        # region Image
        self.img = QLabel()
        self.img.setFixedSize(578, 200)
        self.img.setAlignment(Qt.AlignCenter)
        # endregion
        # region TeX LineEdit
        self.tex = QLineEdit()
        self.tex.setAlignment(Qt.AlignCenter)
        self.tex.setFont(QFont("Cambria Math", 20))
        self.tex.setMaximumHeight(60)
        self.tex.setPlaceholderText("Enter Your Tex Here")
        self.tex.setEchoMode(QLineEdit.Normal)
        self.tex.textChanged.connect(self.on_tex_changed)
        # endregion
        # region PushButtons
        self.save_as_raw_tex = QPushButton("&Raw")
        self.save_as_raw_tex.setFixedHeight(40)
        self.save_as_raw_tex.setFont(QFont("等线", 20))
        self.save_as_raw_tex.clicked.connect(lambda: self.copy_tex_to_clipboard(""))
        self.save_as_inline_tex = QPushButton("&Inline")
        self.save_as_inline_tex.setFixedHeight(40)
        self.save_as_inline_tex.setFont(QFont("等线", 20))
        self.save_as_inline_tex.clicked.connect(lambda: self.copy_tex_to_clipboard("$"))
        self.save_as_block_tex = QPushButton("&Block")
        self.save_as_block_tex.setFixedHeight(40)
        self.save_as_block_tex.setFont(QFont("等线", 20))
        self.save_as_block_tex.clicked.connect(lambda: self.copy_tex_to_clipboard("$$"))
        self.open_img = QPushButton("&Open")
        self.open_img.setFixedHeight(40)
        self.open_img.setFont(QFont("等线", 20))
        self.open_img.clicked.connect(lambda: self.get_tex(self.get_img()))
        self.snap_img = QPushButton("&Snap")
        self.snap_img.setFixedHeight(40)
        self.snap_img.setFont(QFont("等线", 20))
        self.snap_img.clicked.connect(self.capture_img)
        self.draw_img = QPushButton("&Draw")
        self.draw_img.setFixedHeight(40)
        self.draw_img.setFont(QFont("等线", 20))
        self.draw_img.clicked.connect(self.canvas_img)
        # endregion
        # region Layout
        self.copy_hlo = QHBoxLayout()
        self.open_hlo = QHBoxLayout()
        self.copy_hlo.addWidget(self.save_as_raw_tex)
        self.copy_hlo.addWidget(self.save_as_inline_tex)
        self.copy_hlo.addWidget(self.save_as_block_tex)
        self.open_hlo.addWidget(self.open_img)
        self.open_hlo.addWidget(self.snap_img)
        self.open_hlo.addWidget(self.draw_img)
        self.vlo = QVBoxLayout()
        self.vlo.addWidget(self.svg_container)
        self.vlo.addWidget(self.img)
        self.vlo.addWidget(self.label)
        self.vlo.addWidget(self.tex)
        self.vlo.addLayout(self.copy_hlo)
        self.vlo.addLayout(self.open_hlo)
        # endregion
        self.get_tex("")
        self.setLayout(self.vlo)

    def on_tex_changed(self):
        try:
            parser = math_text.MathTextParser('svg')
            parser.parse(r"$" + self.tex.text() + r"$")
        except ValueError:
            self.label.setText("TeX语法不正确")
        else:
            self.label.setText('')
            self.generate_svg(self.tex.text())

    def copy_tex_to_clipboard(self, string):
        clipboard = QApplication.clipboard()
        clipboard.setText(string + self.tex.text() + string)
        self.label.setText("TeX已复制至剪贴板")

    def generate_svg(self, raw_tex):
        fig = Figure(figsize=(5, 4), dpi=300)
        canvas = FigureCanvasAgg(fig)
        fig.text(.5, .5, r"$" + raw_tex + r"$", fontsize=40)
        fig.savefig("output.svg", bbox_inches="tight", facecolor=(1, 1, 1, 0))
        self.svg.load("output.svg")
        renderer = QSvgRenderer('output.svg').defaultSize()
        w = renderer.width()
        h = renderer.height()
        if w / h > 578 / 200:
            display_w = 578
            display_h = int(578 * h / w)
        else:
            display_h = 200
            display_w = int(200 * w / h)
        self.svg.setFixedWidth(display_w)
        self.svg.setFixedHeight(display_h)
        self.svg.setGeometry(QRect(289 - int(display_w / 2), 100 - int(display_h / 2), display_w, display_h))

    def get_img(self):
        file_name, file_type = QFileDialog.getOpenFileName(self, "选取图片", "./", "所有文件 (*);;图片文件 (*.jpg *.png)")
        print(file_name, file_type)
        return file_name

    def get_tex(self, url=r"limit.jpg"):
        if url == "":
            self.set_data("limit.jpg", r"\lim_{x\rightarrow3}(\frac{x^{2}+9}{x-3})", 1)
            return
        with open(url, 'rb') as pic:
            base64_data = base64.b64encode(pic.read())
            print(base64_data)
        img_url = "data:image/jpg;base64," + base64_data.decode()
        r = requests.post("https://api.mathpix.com/v3/latex", data=json.dumps({'url': img_url}),
                          headers={"app_id": "******", "app_key": "********************************",
                                   "Content-type": "application/json"})
        print(json.dumps(json.loads(r.text), indent=4, sort_keys=True))
        try:
            raw_data = json.loads(r.text)
        except AttributeError:
            return
        else:
            if "latex" in raw_data:
                tex = raw_data["latex"]
            else:
                return
            if "latex_confidence" in raw_data:
                confidence = raw_data["latex_confidence"]
            else:
                confidence = 1

            self.set_data(url, tex, confidence)

    def set_data(self, img, tex, con):
        raw_img = QPixmap(img)
        w = raw_img.width()
        h = raw_img.height()
        if w / h > 578 / 200:
            self.img.setPixmap(raw_img.scaledToWidth(578, Qt.SmoothTransformation))
        else:
            self.img.setPixmap(raw_img.scaledToHeight(200, Qt.SmoothTransformation))

        tex_data = tex
        tex_data = tex_data.replace(r"\\", "\\")
        tex_data = tex_data.replace(' ', '')
        self.tex.setText(tex_data)
        self.generate_svg(tex_data)

        if con < 0.8:
            self.label.setText("置信值低于0.8, 建议进行人工校对 : ")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        print("dropped")
        url = str(event.mimeData().urls()[0].toLocalFile())
        print(url)
        self.get_tex(url)

    def capture_img(self):
        self.capture.grab_new_img()
        self.capture.show()
        self.capture.captured.connect(lambda: self.get_tex("capture.jpg"))

    def canvas_img(self):
        self.draw.show()
        self.draw.drawn.connect(lambda: self.get_tex("canvas.jpg"))


class Capture(QWidget):
    captured = pyqtSignal()

    def __init__(self, parent=None):
        super(Capture, self).__init__(parent)
        self.setWindowTitle("MathPix+ - 截屏")
        self.setMouseTracking(True)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowActive | Qt.WindowFullScreen)
        self.setWindowIcon(QIcon("favicon.ico"))
        self.loadImg = QPixmap()
        self.capturedImg = QPixmap()
        self.screenWidth = 0
        self.screenHeight = 0
        self.isMousePressed = False
        self.beginPoint = QPoint(0, 0)
        self.endPoint = QPoint(0, 0)
        self.painter = QPainter()

    def grab_new_img(self):
        self.loadImg = QScreen.grabWindow(QApplication.primaryScreen(), QApplication.desktop().winId())
        self.capturedImg = QPixmap()
        self.screenWidth = self.loadImg.width()
        self.screenHeight = self.loadImg.height()
        self.isMousePressed = False
        self.beginPoint = QPoint(0, 0)
        self.endPoint = QPoint(0, 0)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.isMousePressed = True
            self.beginPoint = event.pos()
        if event.button() == Qt.RightButton:
            self.isMousePressed = False
            self.beginPoint = QPoint(0, 0)
            self.endPoint = QPoint(0, 0)
            self.update()

    def mouseMoveEvent(self, event):
        if self.isMousePressed:
            self.endPoint = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.endPoint = event.pos()
        self.isMousePressed = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return or Qt.Key_Enter:
            self.capturedImg.save("capture.jpg", "JPG")
            self.captured.emit()
            self.close()

    def paintEvent(self, event):
        self.painter.begin(self)
        shadow_color = QColor(0, 0, 0, 100)
        self.painter.setPen(QPen(Qt.black, 2, Qt.SolidLine, Qt.FlatCap))
        self.painter.drawPixmap(0, 0, self.loadImg)
        self.painter.fillRect(self.loadImg.rect(), shadow_color)
        if self.isMousePressed:
            selected_rect = QRect(min(self.beginPoint.x(), self.endPoint.x()),
                                  min(self.beginPoint.y(), self.endPoint.y()),
                                  max(1, abs(self.beginPoint.x() - self.endPoint.x())),
                                  max(1, abs(self.beginPoint.y() - self.endPoint.y())))
            self.capturedImg = self.loadImg.copy(selected_rect)
            self.painter.drawPixmap(selected_rect.topLeft(), self.capturedImg)
            self.painter.drawRect(selected_rect)
        self.painter.end()


class Canvas(QWidget):
    drawn = pyqtSignal()

    def __init__(self, parent=None):
        super(Canvas, self).__init__(parent)
        self.setWindowTitle("MathPix+ - 画板")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowState(Qt.WindowActive | Qt.WindowFullScreen)
        self.setWindowIcon(QIcon("favicon.ico"))
        self.setFixedSize(QApplication.desktop().screenGeometry().width(),
                          QApplication.desktop().screenGeometry().height())
        self.canvas = QPixmap(QApplication.desktop().screenGeometry().width(),
                              QApplication.desktop().screenGeometry().height())
        self.canvas.fill(Qt.white)
        self.penSize = 8
        self.pen = QPen(Qt.black, self.penSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setCursor(Qt.CrossCursor)
        self.lastPoint = QPoint()
        self.endPoint = QPoint()

    def paintEvent(self, event):
        painter = QPainter(self.canvas)
        painter.setPen(self.pen)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.drawLine(self.lastPoint, self.endPoint)
        self.lastPoint = self.endPoint
        pix_painter = QPainter(self)
        pix_painter.drawPixmap(0, 0, self.canvas)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lastPoint = event.pos()
            self.endPoint = self.lastPoint

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton:
            self.endPoint = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.endPoint = event.pos()
            self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            self.canvas.fill(Qt.white)
            self.update()
        elif event.key() == Qt.Key_Escape:
            self.canvas.fill(Qt.white)
            self.update()
            self.close()
        elif event.key() == Qt.Key_Return or Qt.Key_Enter:
            self.canvas.save("canvas.jpg", "JPG")
            self.canvas.fill(Qt.white)
            self.update()
            self.drawn.emit()
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Result(None)
    window.show()
    sys.exit(app.exec_())
