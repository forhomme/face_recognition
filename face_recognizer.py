import cv2
import threading
from mysql_connection import TambahKaryawan


class FaceRecognizer:
    def __init__(self):
        # init for face recognizer and detector
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read('trainer.yml')
        font = cv2.FONT_HERSHEY_SIMPLEX
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + '/haarcascade_frontalface_default.xml')
        self.recognizer = recognizer
        self.font = font

        # initialize and start real time video capture
        cam = cv2.VideoCapture(0)
        cam.set(3, 640)
        cam.set(3, 480)
        self.cam = cam

        # Define min window size to be recognized as a face
        minW = 0.1 * cam.get(3)
        minH = 0.1 * cam.get(4)
        self.minW = minW
        self.minH = minH

        # Define mysql connection
        karyawan = TambahKaryawan()

    def predict_face(self, event):
        while True:
            ret, frame = self.cam.read()
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
                if confidence <= 100:
                    if event:

                    name = id
                    confidence = f"  {round(100 - confidence)}%"
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

            # show the video and press q for quit
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def release_video(self):
        self.cam.release()
        cv2.destroyAllWindows()
        print("\n [INFO] Exiting Program and cleanup stuff")