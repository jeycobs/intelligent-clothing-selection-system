import os
import torch
from transformers import CLIPProcessor, CLIPVisionModelWithProjection
from PIL import Image
from rembg import remove, new_session 

os.environ["TOKENIZERS_PARALLELISM"] = "false"

class StyleFeatureExtractor:
    def __init__(self):
        print("загрузка FashionCLIP...")
        self.model_id = "patrickjohncyh/fashion-clip" 
        
        if torch.backends.mps.is_available():
            self.device = "mps"
            print("pyorch: Apple M2 (MPS) АКТИВЕН!")
        else:
            self.device = "cpu"
            
        self.model = CLIPVisionModelWithProjection.from_pretrained(self.model_id).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(self.model_id)
        self.model.eval()

        print("Инициализация модуля удаления фона (rembg)...")
        self.rembg_session = new_session("u2net")

    def get_embedding(self, image: Image.Image):
        clean_image = remove(image, session=self.rembg_session).convert("RGB")
        
        #извлекаем вектор стиля
        inputs = self.processor(images=clean_image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            image_features = outputs.image_embeds 
            
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        return image_features.cpu().numpy().flatten()