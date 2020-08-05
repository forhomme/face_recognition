from PyQt5 import QtGui
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication, QLabel, QGridLayout, QMessageBox
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
from mysql_connection import TambahKaryawan
import multiprocessing
from face_recognizer import FaceRecognizer


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self._event = False

        # init for face recognizer and detector
        recognize = FaceRecognizer()
        self.recognize = recognize

        # Define mysql connection
        karyawan = TambahKaryawan()
        self.karyawan = karyawan

        # define queue for multiprocessing
        q = multiprocessing.Queue()
        self.q = q

    def get_all_karyawan(self, queue):
        process_karyawan = multiprocessing.Process(target=self.karyawan.get_all_data, args=(queue,))
        process_karyawan.daemon = True
        process_karyawan.start()
        all_karyawan = queue.get()
        process_karyawan.join()
        return all_karyawan

    def run(self):
        names = self.get_all_karyawan(self.q)
        # capture from web cam
        while self._run_flag:
            # Capture frame-by-frame
            ret, frame = self.recognize.cam.read()
            if ret:
                # Our operations on the frame come here
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.recognize.face_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.2,
                    minNeighbors=5,
                    minSize=(int(self.recognize.minW), int(self.recognize.minH)),
                )

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    id, confidence = self.recognize.recognizer.predict(gray[y:y + h, x:x + w])

                    # If confidence is 100 : perfect match
                    if confidence < 100:
                        for index, data in enumerate(names):
                            if data[0] == id:
                                name = data[1]
                        confidence = f"  {round(100 - confidence)}%"
                        if self._event:
                            pass

                    else:
                        name = "unknown"
                        confidence = f"  {round(100 - confidence)}%"

                    cv2.putText(
                        frame,
                        str(name),
                        (x + 5, y - 5),
                        self.recognize.font,
                        1,
                        (255, 255, 255),
                        2
                    )
                    cv2.putText(
                        frame,
                        str(confidence),
                        (x + 5, y + h - 5),
                        self.recognize.font,
                        1,
                        (255, 255, 0),
                        1
                    )

                self.change_pixmap_signal.emit(frame)
        # shut down capture system
        self.recognize.cam.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.karyawan.close_connection()
        self.q.close()
        self.wait()
        print("Close all connection")


# Subclass to define opencv widget
class OpenCvApp(QWidget):
    def __init__(self):
        super().__init__()
        self.disply_width = 640
        self.display_height = 480

        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)

        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


# Subclass QMainWindow to customise application's main window
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Absen Demo")
        self.setGeometry(400, 200, 800, 600)

        layout = QGridLayout()
        self.central_widget = OpenCvApp()

        layout.addWidget(self.central_widget, 0, 0)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def closeEvent(self, event):
        result = QMessageBox.question(self,
                                            "Confirm Exit",
                                            "Are you sure you want to exit ?",
                                            QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            event.accept()
            self.central_widget.closeEvent(event)
        else:
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = MainWindow()
    a.show()
    sys.exit(app.exec_())