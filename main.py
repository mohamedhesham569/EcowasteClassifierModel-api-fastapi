from fastapi import FastAPI, HTTPException,Depends, File, UploadFile
import uvicorn
from app import crud,auth,models,schemas
from sqlalchemy.orm import Session
from app.database import SessionLocal,engine,get_db
from waste_classifier.model import classify_waste
from fastapi.middleware.cors import CORSMiddleware


models.Base.metadata.create_all(bind=engine)
app = FastAPI()

origins=["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


latest_results = []
last_class_name=None

@app.post("/register/")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.post("/login/")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/classify/")
async def classify_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    try:
        image_bytes = await file.read()
        waste_class, confidence = classify_waste(image_bytes)
        
        db_result = schemas.ClassificationResultCreate(
            class_name=waste_class,
            confidence=confidence,
            user_id=current_user.id
        )
        crud.create_waste_result(db=db, waste_result=db_result)
        return {"class_name": waste_class, "confidence": confidence}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/")
async def get_results(
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.get_current_user)):
    try:
        results = crud.get_user_results(db, current_user.id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/class_counts/")
async def get_class_counts(
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.get_current_user)):
    try:
        class_counts = crud.get_class_counts(db,current_user.id)
        return {class_name: count for class_name, count in class_counts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os


os.makedirs("temp_images", exist_ok=True)

@app.get("/camera_demo/", response_class=HTMLResponse)
async def camera_demo():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Camera Demo</title>
        <script>
            async function captureImage() {
                const video = document.getElementById('video');
                const canvas = document.getElementById('canvas');
                const resultDiv = document.getElementById('result');
                
                
                canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = canvas.toDataURL('image/jpeg');
                
                
                const blob = await fetch(imageData).then(res => res.blob());
                const formData = new FormData();
                formData.append('file', blob, 'capture.jpg');
                
                const response = await fetch('/classify_demo/', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                resultDiv.innerHTML = `class: ${data.class_name}, acc : ${data.confidence.toFixed(2)}%`;
            }
            
            // تشغيل الكاميرا
            async function startCamera() {
                const video = document.getElementById('video');
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    video.srcObject = stream;
                } catch (err) {
                    console.error("Error accessing camera:", err);
                }
            }
            
            window.onload = startCamera;
        </script>
    </head>
    <body>
        <h1>camera try</h1>
        <video id="video" width="640" height="480" autoplay></video>
        <button onclick="captureImage()">catch and classifiy</button>
        <canvas id="canvas" width="640" height="480" style="display:none;"></canvas>
        <div id="result" style="margin-top:20px; font-size:20px;"></div>
    </body>
    </html>
    """

@app.post("/classify_demo/")
async def classify_demo(
    file: UploadFile = File(...),
):
    try:
        image_bytes = await file.read()
        waste_class, confidence = classify_waste(image_bytes)
        return {"class_name": waste_class, "confidence": confidence}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


#using live camera
# stop_event = threading.Event()

# def run_camera():
#     cap = cv2.VideoCapture(0)
#     while not stop_event.is_set():
#         ret, frame = cap.read()
#         if not ret:
#             print("Error: Could not read frame.")
#             break
#         try:
#             waste_class, confidence = waste_classifier.classify_waste(frame)
#             if isinstance(confidence, np.float32):
#                 confidence = float(confidence)
            
#             if waste_class:
#                 latest_results.append({
#                     "class_name": waste_class,
#                     "confidence": confidence
#                 })
#             cv2.putText(frame, f"{waste_class}: {confidence:.2f}%", (10, 30),
#                         cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#             cv2.imshow("Waste Detection & Classification", frame)

#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
#         except Exception as e:
#             print(f"Error during classification: {e}")
#             break

#     cap.release()
#     cv2.destroyAllWindows()
#     print("Camera stopped.")

# camera_thread = threading.Thread(target=run_camera)
# camera_thread.daemon = True  
# camera_thread.start()

# @app.get("/results/")
# async def get_results(db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user)):
#     try:
        # if not stop_event.is_set():
        #     start_camera(db, current_user)
        # if camera_thread is None or not camera_thread.is_alive():
        #     stop_event.clear()
        #     camera_thread = threading.Thread(target=run_camera)
        #     camera_thread.daemon = True
        #     camera_thread.start()
        # results = []
        # for result in latest_results:
        #     results.append({
        #         "class_name": result["class_name"],
        #         "confidence": float(result["confidence"])
        #     })
#         results = []
#         for result in latest_results:
#             results.append({
#                 "class_name": result["class_name"],
#                 "confidence": float(result["confidence"])
#             })
#         # if latest_results:
#         #     last_result = latest_results[-1]
#         #     db_result = schemas.ClassificationResult(
#         #         user_id=current_user.id,
#         #         class_name=last_result["class_name"],
#         #         confidence=last_result["confidence"]
#         #     )
            
#         #     return crud.create_waste_result(db=db, waste_result=db_result)
#         #     # return {"message": "Result saved successfully."}
#         # else:
#         #     raise HTTPException(status_code=400, detail="No results available to save.")
#         return results
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/stop/")
# async def stop_camera(db: Session = Depends(get_db), current_user: int = Depends(auth.get_current_user)):
#     stop_event.set()
#     return {"message": "Camera stopped."}

# @app.post("/stop/")
# async def stop_camera(db: Session = Depends(get_db),current_user: int = Depends(auth.get_current_user)):
#     stop_event.set()
#     try:
#         if latest_results:
#             last_result = latest_results[-1]
#             db_result = schemas.ClassificationResult(
#                 user_id=current_user.id,
#                 class_name=last_result["class_name"],
#                 confidence=last_result["confidence"]
#             )
            
#             return crud.create_waste_result(db=db, waste_result=db_result)
#             # return {"message": "Result saved successfully."}
#         else:
#             raise HTTPException(status_code=400, detail="No results available to save.")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
