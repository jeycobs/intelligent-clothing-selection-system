import streamlit as st
import requests
from PIL import Image
import os

st.set_page_config(page_title="AI Stylist", layout="wide")

st.title("Интеллектуальная система подбора одежды на основе анализа изображений и цветовых палит")
st.write("Загрузи фото вещи, а нейросеть проанализирует её стиль, выделит цвета и подберет гардероб!")

uploaded_file = st.file_uploader("Выбери фото...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Твой выбор:")
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)

    with col2:
        if st.button("Подобрать образы"):
            with st.spinner("Нейросеть думает (извлекает признаки и ищет в FAISS)..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post("http://localhost:8000/recommend/", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        st.subheader("Доминирующие цвета (K-Means):")
                        colors = data.get("extracted_colors",[])
                        
                        color_html = ""
                        for color in colors:
                            color_html += f'<div style="display:inline-block; background-color:{color}; width:50px; height:50px; border-radius:50%; margin-right:10px; border: 1px solid #ccc; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);"></div>'
                        st.markdown(color_html, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        
                        st.subheader("Рекомендации (Векторный поиск FAISS):")
                        recommendations = data.get("recommendations",[])
                        
                        if not recommendations:
                            st.warning("К сожалению, ничего не найдено.")
                        else:
                            rec_cols = st.columns(len(recommendations))
                            for idx, rec in enumerate(recommendations):
                                item_id = rec["item_id"]
                                score = rec["similarity_score"]
                                img_path = f"images/{item_id}.jpg"
                                
                                with rec_cols[idx]:
                                    if os.path.exists(img_path):
                                        rec_image = Image.open(img_path)
                                        st.image(rec_image, width=200) 
                                        st.caption(f"ID: {item_id} | Сходство: {score:.2f}")
                                    else:
                                        st.error(f"Изображение {item_id} не найдено")
                                        
                    else:
                        st.error(f"Ошибка бэкенда: {response.json().get('detail')}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("Не удалось подключиться к бэкенду. Убедись, что 'python3 main.py' запущен!")