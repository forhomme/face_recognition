import cv2


class CameraOpen:
    def __init__(self):
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)  # set Width
        cap.set(4, 480)  # set Height

        # https://stackoverflow.com/questions/30857908/face-detection-using-cascade-classifier-in-opencv-python
        faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + '/haarcascade_frontalface_default.xml')

        self.cap = cap
        self.faceCascade = faceCascade

    def face_video(self):
        while True:
            # Capture frame-by-frame
            ret, frame = self.cap.read()

            # Our operations on the frame come here
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(20, 20)
            )

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.rectangle(gray, (x, y), (x + w, y + h), (255, 0, 0), 2)
                roi_gray = gray[y:y + h, x:x + w]
                roi_color = frame[y:y + h, x:x + w]

            # Display the resulting frame
            cv2.imshow('frame', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def get_picture(self, face_id):
        count = 0
        while True:
            # Capture frame-by-frame
            ret, frame = self.cap.read()

            # Our operations on the frame come here
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.3,
                minNeighbors=5,
                minSize=(20, 20)
            )

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                count += 1
                # Save the captured image into the datasets folder
                cv2.imwrite("dataset/user." + str(face_id) + "." + str(count) + ".jpg", gray[y:y + h, x:x + w])

            # Display the resulting frame
            cv2.imshow('frame', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            elif count >= 30:  # Take 30 face sample and stop video
                break

    def release_cam(self):
        self.cap.release()
        cv2.destroyAllWindows()


cam = CameraOpen()
cam.face_video()
cam.release_cam()
