import sys
from PyQt5 import QtCore, QtGui, QtWidgets, QtTest
from PyQt5 import uic
import sys
import cv2
import numpy as np
from mysql_connection import TambahKaryawan
from face_recognizer import FaceRecognizer
from face_trainer import TrainPicture
import multiprocessing


# subclass to define opencv video
class VideoThread(QtCore.QThread):
    change_pixmap_signal = QtCore.pyqtSignal(np.ndarray)

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

        # for printing in the Qlabel
        self.name = ""
        self.id = 0

    def get_all_karyawan(self):
        data_karyawan = self.karyawan.get_all_data()
        return data_karyawan

    def run(self):
        names = self.get_all_karyawan()
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
                            input = multiprocessing.Process(target=self.karyawan.insert_absen, args=(id, name))
                            input.daemon = True
                            input.start()
                            input.join()
                            self.name = name
                            self.id = id
                            self._event = False

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
        self.q.close()
        self.wait()


class PhotoThread(QtCore.QThread):
    change_pixmap_signal = QtCore.pyqtSignal(np.ndarray)
    start_recognizer = QtCore.pyqtSignal()
    count_signal = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._run_flag = True

        # init for face recognizer and detector
        recognize = FaceRecognizer()
        self.recognize = recognize

        self.face_id = 0
        self._event = False

    def run(self):
        count = 0
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
                    count += 1
                    # Save the captured image into the datasets folder
                    cv2.imwrite("dataset/user." + str(self.face_id) + "." + str(count) + ".jpg", gray[y:y + h, x:x + w])
                    self.count_signal.emit(count)
                    QtTest.QTest.qWait(50)

                self.change_pixmap_signal.emit(frame)

                if count >= 30:
                    self.stop()
                    self.start_recognizer.emit()
        # shut down capture system
        self.recognize.cam.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()
        print("Done")


# Subclass to define face recognizer widget
class RecognizeApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.disply_width = 640
        self.display_height = 480

        # create the label that holds the image
        self.image_label = QtWidgets.QLabel(self)
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

    @QtCore.pyqtSlot(np.ndarray)
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
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, QtCore.Qt.KeepAspectRatio)
        return QtGui.QPixmap.fromImage(p)


# subclass to take photo for training
class TrainApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.disply_width = 640
        self.display_height = 480

        # create the label that holds the image
        self.image_label = QtWidgets.QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)

        # create the video capture thread
        self.thread = PhotoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @QtCore.pyqtSlot(np.ndarray)
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
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, QtCore.Qt.KeepAspectRatio)
        return QtGui.QPixmap.fromImage(p)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("test.ui", self)

        self.setWindowTitle("Absen Demo")
        self.app = RecognizeApp()
        self.photoApp = QtWidgets.QWidget()

        # set layout in Qwidget and add OpenCv to the widget
        self.app_layout = QtWidgets.QHBoxLayout()
        self.app_layout.addWidget(self.app)
        self.videoApp.setLayout(self.app_layout)

        self.absenButton.clicked.connect(self.absenMysql)
        self.photoButton.clicked.connect(self.photoPreparation)
        self.inputNikButton.clicked.connect(self.takePhoto)
        self.trainButton.clicked.connect(self.train_picture)
        self.inputNikButton.hide()
        self.inputNikLine.hide()
        self.nikLabel.hide()

    def absenMysql(self):
        self.app.thread._event = True
        QtTest.QTest.qWait(2000)
        self.statusLabel.setText(f"Selamat datang {self.app.thread.name}")

    def photoPreparation(self):
        self.app.thread.stop()
        self.app_layout.removeWidget(self.app)
        self.openCv.setCurrentWidget(self.pictureApp)
        self.inputNikButton.show()
        self.inputNikLine.show()
        self.nikLabel.show()
        self.statusLabel.setText("Input Nik karyawan")

    def takePhoto(self):
        self.statusLabel.setText("Persiapan pengambilan foto")
        QtTest.QTest.qWait(1000)
        self.statusLabel.setText("1")
        QtTest.QTest.qWait(1000)
        self.statusLabel.setText("2")
        QtTest.QTest.qWait(1000)
        self.statusLabel.setText("3")
        QtTest.QTest.qWait(1000)

        # set layout in Qwidget and add OpenCv to the widget
        self.photoApp = TrainApp()
        self.photoApp.thread.face_id = self.inputNikLine.text()
        self.photo_layout = QtWidgets.QHBoxLayout()
        self.photo_layout.addWidget(self.photoApp)
        self.pictureApp.setLayout(self.photo_layout)

        # emit signal
        self.photoApp.thread.count_signal.connect(self.print_count)
        self.photoApp.thread.start_recognizer.connect(self.endOfPhoto)

    @QtCore.pyqtSlot()
    def endOfPhoto(self):
        self.statusLabel.setText("Done")
        self.photo_layout.removeWidget(self.photoApp)

        self.inputNikButton.hide()
        self.inputNikLine.hide()
        self.nikLabel.hide()

    @QtCore.pyqtSlot(int)
    def print_count(self, count):
        self.statusLabel.setText(f"Pengambilan wajah {count}")

    def train_picture(self):
        self.statusLabel.setText("Prose training wajah")
        QtTest.QTest.qWait(1000)
        train_app = TrainPicture()
        samples, ids = train_app.get_image_and_label()
        train_app.train_and_save(samples, ids)
        self.statusLabel.setText("Proses selesai")

        # change to absent video again
        self.openCv.setCurrentWidget(self.videoApp)
        self.app = RecognizeApp()

        # set layout in Qwidget and add OpenCv to the widget
        self.app_layout.addWidget(self.app)
        self.videoApp.setLayout(self.app_layout)

    def closeEvent(self, event):
        result = QtWidgets.QMessageBox.question(self,
                                            "Confirm Exit",
                                            "Are you sure you want to exit ?",
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.Yes:
            event.accept()
            self.app.closeEvent(event)
        else:
            event.ignore()


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()