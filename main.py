import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
import io, faiss, numpy as np
import json
import random
import uuid

from ml_model import StyleFeatureExtractor
from color_module import ColorAnalyzer
from database import SessionLocal, ItemMeta, User, SavedOutfit

app = FastAPI(title="Fashion AI Social Network")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#папка для загрузок юзеров
os.makedirs("images/uploads", exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

print("Загрузка моделей анализа...")
extractor = StyleFeatureExtractor()
color_analyzer = ColorAnalyzer(n_colors=1)

if os.path.exists("fashion_index.faiss"):
    index = faiss.read_index("fashion_index.faiss")
    with open("vector_map.txt", "r", encoding="utf-8", errors="ignore") as f:
        vector_map =[line.strip('\ufeff\r\n\t ') for line in f.readlines()]
    print(f"✅ FAISS загружен: {index.ntotal} векторов")


@app.post("/register/")
async def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    if db.query(User).filter((User.email == email) | (User.username == username)).first():
        db.close()
        raise HTTPException(status_code=400, detail="Пользователь с таким Email или Логином уже существует")
    
    new_user = User(username=username, email=email, hashed_password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    return {"token": new_user.id, "username": new_user.username}

@app.post("/login/")
async def login(email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user or user.hashed_password != password:
        db.close()
        raise HTTPException(status_code=400, detail="Неверный Email или пароль")
    db.close()
    return {"token": user.id, "username": user.username}

@app.post("/forgot-password/")
async def forgot_password(email: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="Email не найден")
    
    reset_token = str(random.randint(100000, 999999)) # 6-значный код
    user.reset_token = reset_token
    db.commit()
    db.close()
    
    print(f"\n[EMAIL СЕРВЕР] Письмо отправлено на {email}")
    print(f"Код восстановления: {reset_token}\n")
    return {"message": "Код отправлен на почту"}

@app.post("/reset-password/")
async def reset_password(token: str = Form(...), new_password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        db.close()
        raise HTTPException(status_code=400, detail="Неверный код")
    user.hashed_password = new_password
    user.reset_token = None
    db.commit()
    db.close()
    return {"status": "success"}


@app.get("/feed/")
async def get_feed(color: str = None, user_id: int = None):
    db = SessionLocal()
    query = db.query(SavedOutfit).order_by(SavedOutfit.timestamp.desc())
    if color:
        query = query.filter(SavedOutfit.dominant_color == color)
    outfits = query.limit(100).all()
    
    fav_colors =[]
    #если юзер авторизован, изучаем его вкусы
    if user_id:
        user_outfits = db.query(SavedOutfit).filter(SavedOutfit.user_id == user_id).all()
        fav_colors =[o.dominant_color for o in user_outfits]

    result =[]
    for o in outfits:
        #логика рекомендаций: если цвет есть в любимых у юзера, и это чужой лук
        is_rec = False
        if user_id and o.dominant_color in fav_colors and o.user_id != user_id:
            is_rec = True
            
        result.append({
            "id": o.id,
            "author_name": o.author_name,
            "dominant_color": o.dominant_color,
            "original": o.original_image_url,
            "items": json.loads(o.items_json) if o.items_json else[],
            "is_recommended": is_rec
        })
        
    #сортируем: сначала РЕКОМЕНДОВАННЫЕ, потом обычные (Timsort сохраняет сортировку по времени)
    if user_id:
        result.sort(key=lambda x: x["is_recommended"], reverse=True)

    db.close()
    return {"feed": result}

@app.get("/profile/{user_id}")
async def get_profile(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user: return {"error": "Юзер не найден"}
    outfits = db.query(SavedOutfit).filter(SavedOutfit.user_id == user_id).order_by(SavedOutfit.timestamp.desc()).all()
    result =[{"id": o.id, "color": o.dominant_color, "original": o.original_image_url, "items": json.loads(o.items_json)} for o in outfits]
    db.close()
    return {"username": user.username, "outfits": result}


@app.post("/generate_combinations/")
async def generate_combinations(file: UploadFile = File(...)):
    #сохраняем фотку юзера, чтобы показывать в профиле
    image_bytes = await file.read()
    upload_filename = f"uploads/{uuid.uuid4().hex}.jpg"
    with open(f"images/{upload_filename}", "wb") as f:
        f.write(image_bytes)
    original_url = f"http://localhost:8000/images/{upload_filename}"

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    main_color = color_analyzer.get_dominant_colors(image)[0]
    query_vector = extractor.get_embedding(image)
    
    query_matrix = np.array([query_vector]).astype('float32')
    distances, indices = index.search(query_matrix, 50) 
    
    db = SessionLocal()
    base_items =[]
    for j, idx in enumerate(indices[0]):
        if idx == -1: continue
        item_id = vector_map[idx]
        item_meta = db.query(ItemMeta).filter(ItemMeta.id == item_id).first()
        if not item_meta or item_meta.sub_category in['Innerwear', 'Loungewear', 'Socks', 'Apparel Set']: continue
        base_items.append({"meta": item_meta, "similarity": min(100, max(0, int(distances[0][j] * 100)))})
        if len(base_items) == 5: break

    pool = {
        "Bottomwear": db.query(ItemMeta).filter(ItemMeta.sub_category == "Bottomwear").limit(200).all(),
        "Shoes": db.query(ItemMeta).filter(ItemMeta.sub_category == "Shoes").limit(200).all(),
        "Topwear": db.query(ItemMeta).filter(ItemMeta.sub_category == "Topwear").limit(200).all()
    }
        
    outfit_combinations =[]
    for i, base in enumerate(base_items):
        combo =[]
        base_meta = base["meta"]
        combo.append({"category": base_meta.sub_category, "color": base_meta.color, "id": base_meta.id, "similarity": base["similarity"], "image_url": f"http://localhost:8000/images/{base_meta.id}.jpg"})
        
        needed = ["Topwear", "Bottomwear", "Shoes"]
        if base_meta.sub_category in needed: needed.remove(base_meta.sub_category)
        elif "Topwear" in needed: needed.remove("Topwear") 
            
        for cat in needed:
            if pool[cat] and len(pool[cat]) > 0:
                comp_item = random.choice(pool[cat]) 
                combo.append({"category": comp_item.sub_category, "color": comp_item.color, "id": comp_item.id, "similarity": random.randint(80, 95), "image_url": f"http://localhost:8000/images/{comp_item.id}.jpg"})
                
        outfit_combinations.append({"combo_id": i, "items": combo})
    db.close()
    
    return {"status": "success", "dominant_color": main_color, "original_url": original_url, "combinations": outfit_combinations}

@app.post("/like_outfit/")
async def like_outfit(user_id: int = Form(...), original_url: str = Form(...), dominant_color: str = Form(...), items_json: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Юзер не найден")
        
    new_outfit = SavedOutfit(user_id=user.id, author_name=user.username, original_image_url=original_url, dominant_color=dominant_color, items_json=items_json)
    db.add(new_outfit)
    db.commit()
    db.close()
    return {"status": "saved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)