from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from app import crud, auth, models, schemas
from app.database import get_db, engine
from app.config import settings
from waste_classifier.model import classify_waste, process_camera_frame
from app.checkout import router as checkout_router

# إنشاء الجداول
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(checkout_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

def get_optional_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Optional[schemas.User]:
    """
    ترجع المستخدم إذا كان التوكن صالح.
    إذا لم يأتِ توكن أو كان غير صالح، ترجع None.
    """
    try:
        # نعيد استخدام الدالة الأصلية في auth
        return auth.get_current_user(db=db, token=token)
    except HTTPException:
        return None

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

@app.post("/classify/upload")
async def classify_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[schemas.User] = Depends(get_optional_user)
):
    try:
        image_bytes = await file.read()
        waste_class, confidence = classify_waste(image_bytes)

        # نحفظ في قاعدة البيانات فقط للمستخدمين المسجلين
        if current_user:
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

@app.post("/classify/camera/")
async def classify_camera_frame(
    frame: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[schemas.User] = Depends(get_optional_user)
):
    try:
        frame_bytes = await frame.read()
        waste_class, confidence = process_camera_frame(frame_bytes)

        if current_user:
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
    current_user: schemas.User = Depends(auth.get_current_user)
):
    try:
        return crud.get_user_results(db, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/class_counts/")
async def get_class_counts(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    try:
        counts = crud.get_class_counts(db, current_user.id)
        return {cn: cnt for cn, cnt in counts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
