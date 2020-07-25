from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np
from mysql_connection import TambahKaryawan
import multiprocessing


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self._event = False

        # init for face recognizer and detector
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read('trainer.yml')
        font = cv2.FONT_HERSHEY_SIMPLEX
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + '/haarcascade_frontalface_default.xml')
        self.recognizer = recognizer
        self.font = font

        # initialize and start real time video capture
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(3, 480)
        self.cap = cap

        # Define min window size to be recognized as a face
        minW = 0.1 * cap.get(3)
        minH = 0.1 * cap.get(4)
        self.minW = minW
        self.minH = minH

        # Define mysql connection
        karyawan = TambahKaryawan()
        self.karyawan = karyawan

        # define multiprocessing
        q = multiprocessing.Queue()
        self.q = q

        # get all data
        p = multiprocessing.Process(target=self.karyawan.get_all_data, args=(self.q,))
        self.p = p
        self.p.daemon = True
        self.p.start()
        names = self.q.get()
        self.names = names

    def run(self):
        # capture from web cam
        while self._run_flag:
            # Capture frame-by-frame
            ret, frame = self.cap.read()
            if ret:
                # Our operations on the frame come here
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.2,
                    minNeighbors=5,
                    minSize=(int(self.minW), int(self.minH)),
                )

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    id, confidence = self.recognizer.predict(gray[y:y + h, x:x + w])

                    # If confidence is 100 : perfect match
                    if confidence < 100:
                        for index, data in enumerate(self.names):
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
                        self.font,
                        1,
                        (255, 255, 255),
                        2
                    )
                    cv2.putText(
                        frame,
                        str(confidence),
                        (x + 5, y + h - 5),
                        self.font,
                        1,
                        (255, 255, 0),
                        1
                    )

                self.change_pixmap_signal.emit(frame)
        # shut down capture system
        self.cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.karyawan.close_connection()
        self.q.close()
        self.p.join()
        self.wait()
        print("Close all connection")


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt live label demo")
        self.disply_width = 640
        self.display_height = 480
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)
        # create a text label
        self.textLabel = QLabel('Webcam')

        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.textLabel)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())