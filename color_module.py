import numpy as np
from sklearn.cluster import KMeans
from PIL import Image

class ColorAnalyzer:
    def __init__(self, n_colors=3):
        self.n_colors = n_colors

    def get_dominant_colors(self, image: Image.Image):
        """возвращает RGB коды доминирующих цветов на фото"""

        img = image.copy()
        img.thumbnail((150, 150)) 
        
        img_array = np.array(img)
        if img_array.shape[2] == 4: 
            img_array = img_array[:, :, :3]
            
        pixels = img_array.reshape(-1, 3)

        kmeans = KMeans(n_clusters=self.n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        colors = kmeans.cluster_centers_.astype(int)
        
        hex_colors = ["#{:02x}{:02x}{:02x}".format(c[0], c[1], c[2]) for c in colors]
        return hex_colors
