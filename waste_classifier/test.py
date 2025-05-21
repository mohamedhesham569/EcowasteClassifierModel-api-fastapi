import tensorflow as tf

model = tf.keras.models.load_model("C:/Users/mohamed/Desktop/grad_project/EcowasteClassifierModel-api-fastapi/waste_classifier/waste_classifier_finetuned.h5",compile=False)

print("Model loaded successfully!")
