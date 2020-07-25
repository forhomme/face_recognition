import cv2
import numpy as np
from PIL import Image
import os


class TrainPicture:
    def __init__(self):
        self.path = 'dataset'
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + '/haarcascade_frontalface_default.xml')

    def get_image_and_label(self):
        image_paths = [os.path.join(self.path, f) for f in os.listdir(self.path)]
        face_samples = []
        face_ids = []
        for image in image_paths:
            pil_img = Image.open(image).convert('L')  # grayscale
            img_numpy = np.array(pil_img, 'uint8')
            id = int(os.path.split(image)[-1].split(".")[1])
            faces = self.face_detector.detectMultiScale(img_numpy)
            for (x, y, w, h) in faces:
                face_samples.append(img_numpy[y:y + h, x:x + w])
                face_ids.append(id)
        return face_samples, face_ids

    def train_and_save(self, samples, ids):
        self.recognizer.train(samples, np.array(ids))
        self.recognizer.write('trainer.yml')
        # print the number of faces trained
        print("\n [INFO] {0} faces trained. Exiting Program".format(len(np.unique(ids))))
