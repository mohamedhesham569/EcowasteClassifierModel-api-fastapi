import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
import io
import os 



waste_class_labels = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']

script_dir = os.path.dirname(os.path.abspath(__file__))
# model = tf.keras.models.load_model(os.path.join(script_dir, "waste_classifier_finetuned.h5"))


# script_dir = os.path.dirname(os.path.abspath(__file__))


try:
    model = tf.keras.models.load_model(
        os.path.join(script_dir, "waste_classifier_finetuned.h5"),
        custom_objects={'InputLayer': Input}
    )
except Exception as e:
    print(f"Failed to load model: {str(e)}")
    
    model = tf.keras.models.load_model(
        os.path.join(script_dir, "waste_classifier_finetuned.h5"),
        compile=False
    )


def classify_waste(image_bytes: bytes):
    try:

        img = Image.open(io.BytesIO(image_bytes))
        img = img.resize((224, 224))
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        predictions = model.predict(img_array)
        class_index = np.argmax(predictions)
        waste_class = waste_class_labels[class_index]
        confidence = float(predictions[0][class_index] * 100)
        
        return waste_class, confidence
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")

def process_camera_frame(frame_bytes: bytes):
    """
    Process camera frame bytes (for camera streaming)
    Returns: (class_name, confidence)
    """
    try:
        # Convert bytes to OpenCV format
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Preprocess frame
        frame = cv2.resize(frame, (224, 224))
        frame = frame.astype("float32") / 255.0
        frame = np.expand_dims(frame, axis=0)
        
        # Predict
        predictions = model.predict(frame)
        class_index = np.argmax(predictions)
        confidence = float(predictions[0][class_index] * 100)
        
        return waste_class_labels[class_index], confidence
    except Exception as e:
        raise ValueError(f"Frame processing error: {str(e)}")


# using live camera
# import cv2
# import numpy as np
# import tensorflow as tf
# import os

# class WasteClassifier:
#     def __init__(self):
#         script_dir = os.path.dirname(os.path.abspath(__file__))
#         self.net = cv2.dnn.readNet(
#             os.path.join(script_dir, "yolov3.weights"),
#             os.path.join(script_dir, "yolov3.cfg")
#         )
#         with open(os.path.join(script_dir, "coco.names"), "r") as f:
#             self.classes = f.read().strip().split("\n")
        
#         self.waste_related_classes = ["bottle", "cup", "can", "bowl", "book", "bag"]
#         self.waste_model = tf.keras.models.load_model(
#             os.path.join(script_dir, "waste_classifier_finetuned.h5")
#         )
        
#         self.waste_class_labels = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash']     
#         self.layer_names = self.net.getLayerNames()
#         self.output_layers = [self.layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]

#     def preprocess_image(self, img):
#         img = cv2.resize(img, (224, 224))
#         img = img.astype("float32") / 255.0
#         img = np.expand_dims(img, axis=0)
#         return img

#     def detect_objects(self, frame):
#         height, width, _ = frame.shape
#         blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
#         self.net.setInput(blob)
#         outs = self.net.forward(self.output_layers)

#         class_ids = []
#         confidences = []
#         boxes = []

#         for out in outs:
#             for detection in out:
#                 scores = detection[5:]
#                 class_id = np.argmax(scores)
#                 confidence = scores[class_id]

#                 if confidence > 0.5 and self.classes[class_id] in self.waste_related_classes:
#                     center_x = int(detection[0] * width)
#                     center_y = int(detection[1] * height)
#                     w = int(detection[2] * width)
#                     h = int(detection[3] * height)

#                     x = int(center_x - w / 2)
#                     y = int(center_y - h / 2)

#                     if w > 50 and h > 50:
#                         boxes.append([x, y, w, h])
#                         confidences.append(float(confidence))
#                         class_ids.append(class_id)

#         indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
#         return indices, boxes, class_ids

#     def classify_waste(self, frame):
#         indices, boxes, class_ids = self.detect_objects(frame)

#         if len(indices) > 0:
#             for i in indices.flatten():
#                 box = boxes[i]
#                 x, y, w, h = box

#                 if class_ids[i] < len(self.classes):
#                     class_name = self.classes[class_ids[i]]
#                 else:
#                     class_name = "Unknown"

#                 cropped_img = frame[y:y + h, x:x + w]

#                 if cropped_img.shape[0] > 0 and cropped_img.shape[1] > 0:
#                     preprocessed_img = self.preprocess_image(cropped_img)
#                     predictions = self.waste_model.predict(preprocessed_img)
#                     class_index = np.argmax(predictions)
#                     waste_class = self.waste_class_labels[class_index]
#                     confidence = predictions[0][class_index] * 100

#                     if confidence < 60:
#                         waste_class = "Uncertain"

#                     return waste_class, confidence
#         else:
            
#             preprocessed_img = self.preprocess_image(frame)
#             predictions = self.waste_model.predict(preprocessed_img)
#             class_index = np.argmax(predictions)
#             waste_class = self.waste_class_labels[class_index]
#             confidence = predictions[0][class_index] * 100

#             return waste_class, confidence
        
    
# def run_camera_demo():
#     classifier = WasteClassifier()
#     cap = cv2.VideoCapture(0)
    
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
            
        
#         waste_class, confidence = classifier.classify_waste(frame)
        
        
#         label = f"{waste_class}: {confidence:.2f}%"
#         cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#         cv2.imshow("Waste Classification Demo", frame)
        
        
#         if cv2.waitKey(1) & 0xFF == 27:
#             break
    
#     cap.release()
#     cv2.destroyAllWindows()