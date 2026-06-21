import faiss
import numpy as np

class RecommenderSystem:
    def __init__(self, embedding_dim=512):
        self.index = faiss.IndexFlatIP(embedding_dim)
        self.items_meta =[] 

    def build_index(self, embeddings_list: list, meta_list: list):
        if not embeddings_list:
            print("Внимание: Список эмбеддингов пуст!")
            return
            
        embeddings_matrix = np.array(embeddings_list).astype('float32')
        self.index.add(embeddings_matrix)
        self.items_meta.extend(meta_list)
        print(f"В базу добавлено {self.index.ntotal} вещей.")

    def search_similar(self, query_embedding: np.ndarray, top_k=5):
        if self.index.ntotal == 0:
            return []
            
        query_matrix = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_matrix, top_k)
        
        results = []
        for j, idx in enumerate(indices[0]):
            if idx != -1: 
                meta_info = self.items_meta[idx]
                results.append({
                    "item_id": meta_info["id"],
                    "category": meta_info.get("category", "Unknown"),
                    "sub_category": meta_info.get("sub_category", "Unknown"),
                    "color": meta_info.get("color", "Unknown"),
                    "similarity_score": float(distances[0][j])
                })
        return results
