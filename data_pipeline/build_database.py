import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

import pandas as pd
import faiss
import numpy as np
from tqdm import tqdm
from PIL import Image

from ml_model import StyleFeatureExtractor
from database import SessionLocal, ItemMeta, engine, Base

def main():
    print("очистка старой базы...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("загрузка CSV с метаданными...")
    df = pd.read_csv("styles.csv", on_bad_lines='skip').head(100)
    
    extractor = StyleFeatureExtractor()
    embedding_dim = 512
    index = faiss.IndexFlatIP(embedding_dim)
    
    embeddings = []
    vector_id_map =[] #связь индекса faiss и id картинки

    print(f"извлечение признаков (FashionCLIP)...")
    for idx, row in tqdm(df.iterrows(), total=df.shape[0]):
        item_id = str(row['id'])
        img_path = f"images/{item_id}.jpg"
        
        if not os.path.exists(img_path):
            continue 
            
        try:
            image = Image.open(img_path).convert("RGB")
            vector = extractor.get_embedding(image)
            embeddings.append(vector)
            vector_id_map.append(item_id)
            
            #сохраняем мету в базу SQLite
            db_item = ItemMeta(
                id=item_id,
                category=str(row.get('masterCategory', 'Unknown')),
                sub_category=str(row.get('subCategory', 'Unknown')),
                color=str(row.get('baseColour', 'Unknown'))
            )
            db.merge(db_item)
            
        except Exception as e:
            pass #пропускаем битые фото
            
        #сохраняем пачками, чтобы не перегружать ОЗУ
        if len(embeddings) % 1000 == 0:
            db.commit()

    db.commit()
    db.close()

    print("построение индекса FAISS...")
    index.add(np.array(embeddings).astype('float32'))
    faiss.write_index(index, "fashion_index.faiss")
    
    #сохраняем маппинг
    with open("vector_map.txt", "w") as f:
        for v_id in vector_id_map:
            f.write(f"{v_id}\n")

    print("созданы fashion_index.faiss и fashion_metadata.db")

if __name__ == "__main__":
    main()
