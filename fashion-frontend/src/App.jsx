import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const[username, setUsername] = useState(localStorage.getItem('username'));
  const [view, setView] = useState('feed'); 
  
  const [feed, setFeed] = useState([]);
  const[profileData, setProfileData] = useState(null);
  
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const[combinationsData, setCombinationsData] = useState(null);

  const [authForm, setAuthForm] = useState({ user: '', email: '', pass: '', code: '' });

  useEffect(() => {
    if (view === 'feed') fetchFeed();
    if (view === 'profile') fetchProfile();
  }, [view]);

  //запрос ленты с передачей ID пользователя для персональных рекомендаций
  const fetchFeed = async (color = '') => {
    let url = `http://localhost:8000/feed/?`;
    if (color) url += `color=${encodeURIComponent(color)}&`;
    if (token) url += `user_id=${token}`;
    
    const res = await fetch(url);
    const data = await res.json();
    setFeed(data.feed);
  };

  const fetchProfile = async () => {
    const res = await fetch(`http://localhost:8000/profile/${token}`);
    const data = await res.json();
    setProfileData(data);
  };

  const handleAuth = async (endpoint) => {
    const formData = new FormData();
    formData.append("password", authForm.pass);
    if (endpoint === 'register') {
      formData.append("username", authForm.user);
      formData.append("email", authForm.email);
    } else {
      formData.append("email", authForm.email);
    }

    try {
      const res = await fetch(`http://localhost:8000/${endpoint}/`, { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) {
        setToken(data.token); setUsername(data.username);
        localStorage.setItem('token', data.token); localStorage.setItem('username', data.username);
        setView('feed');
      } else { alert(data.detail); }
    } catch (e) { alert("Ошибка сервера"); }
  };

  const handleGenerate = async () => {
    if (!file) return alert("Загрузите фото!");
    setLoading(true);
    const formData = new FormData(); formData.append("file", file);
    try {
      const res = await fetch("http://localhost:8000/generate_combinations/", { method: "POST", body: formData });
      setCombinationsData(await res.json());
    } catch (e) { alert("Ошибка сети."); }
    setLoading(false);
  };

  const handleLike = async (combo) => {
    if (!token) return alert("Войдите в аккаунт!");
    const formData = new FormData();
    formData.append("user_id", token);
    formData.append("original_url", combinationsData.original_url);
    formData.append("dominant_color", combinationsData.dominant_color);
    formData.append("items_json", JSON.stringify(combo.items));
    
    await fetch("http://localhost:8000/like_outfit/", { method: "POST", body: formData });
    alert("Аутфит сохранен в вашу коллекцию!");
    setView('profile');
  };

  const logout = () => { localStorage.clear(); setToken(null); setUsername(null); setView('feed'); };

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="logo" onClick={() => {fetchFeed(''); setView('feed');}}>AI-Stylist</div>
        <div className="nav-buttons">
          <button onClick={() => {fetchFeed(''); setView('feed');}} className="nav-btn">Лента</button>
          {token ? (
            <>
              <button onClick={() => {setView('generate'); setCombinationsData(null);}} className="nav-btn create-btn">Создать Образ</button>
              <button onClick={() => setView('profile')} className="nav-btn">Мой Профиль</button>
              <button onClick={logout} className="nav-btn outline">Выйти</button>
            </>
          ) : (
            <button onClick={() => setView('login')} className="nav-btn primary">Войти</button>
          )}
        </div>
      </nav>

      <main className="content">
        {/* АВТОРИЗАЦИЯ И ГЕНЕРАЦИЯ (Скрыто для краткости, они остались как были) */}
        {view === 'login' && (
          <div className="auth-box">
            <h2>Вход</h2>
            <input placeholder="Email" onChange={e => setAuthForm({...authForm, email: e.target.value})} />
            <input type="password" placeholder="Пароль" onChange={e => setAuthForm({...authForm, pass: e.target.value})} />
            <button className="generate-action-btn" onClick={() => handleAuth('login')}>Войти</button>
            <p className="auth-link" onClick={() => setView('register')}>Нет аккаунта? Зарегистрироваться</p>
          </div>
        )}
        
        {view === 'register' && (
          <div className="auth-box">
            <h2>Регистрация</h2>
            <input placeholder="Имя пользователя" onChange={e => setAuthForm({...authForm, user: e.target.value})} />
            <input placeholder="Email" onChange={e => setAuthForm({...authForm, email: e.target.value})} />
            <input type="password" placeholder="Пароль" onChange={e => setAuthForm({...authForm, pass: e.target.value})} />
            <button className="generate-action-btn" onClick={() => handleAuth('register')}>Создать аккаунт</button>
            <p className="auth-link" onClick={() => setView('login')}>Уже есть аккаунт? Войти</p>
          </div>
        )}

        {view === 'generate' && !combinationsData && (
          <div className="generate-box">
            <h2>Студия стиля 🎨</h2>
            <p>Загрузите фото. Нейросеть мгновенно предложит 5 вариантов сочетаний.</p>
            <input type="file" onChange={e => setFile(e.target.files[0])} />
            <button onClick={handleGenerate} disabled={loading} className="generate-action-btn">
              {loading ? "Анализируем базу..." : "Сгенерировать комбинации"}
            </button>
          </div>
        )}

        {/* ОКНО ВЫБОРА СГЕНЕРИРОВАННЫХ АУТФИТОВ */}
        {view === 'generate' && combinationsData && (
          <div className="combinations-container">
            <h2>Предложенные аутфиты (выберите лучший):</h2>
            <div className="combo-grid">
              {combinationsData.combinations.map((combo) => (
                <div key={combo.combo_id} className="combo-card">
                  <div className="combo-images">
                    {combo.items.map((item, i) => (
                      <div key={i} className={`combo-item item-${i}`}>
                        <img src={item.image_url} alt="clothing" />
                        <div className="sim-badge">{item.similarity}% сходство</div>
                      </div>
                    ))}
                  </div>
                  <button className="like-btn" onClick={() => handleLike(combo)}>❤️ Сохранить в профиль</button>
                </div>
              ))}
            </div>
            <button onClick={() => setCombinationsData(null)} className="nav-btn outline" style={{marginTop:'20px'}}>Загрузить другое фото</button>
          </div>
        )}

        {/* НОВЫЙ ЛИЧНЫЙ ПРОФИЛЬ (РАЗДЕЛЕННЫЕ ОКНА) */}
        {view === 'profile' && profileData && (
          <div className="profile-container">
            <div className="profile-header">
              <h1>Гардероб {profileData.username}</h1>
              <p>Ваши сохраненные идеи и луки</p>
            </div>
            
            <div className="history-list">
              {profileData.outfits.map((outfit) => (
                <div key={outfit.id} className="profile-outfit-window">
                  {/* Левая часть: Исходник */}
                  <div className="profile-left-pane">
                    <img src={outfit.original} alt="Idea" className="profile-orig-img" />
                    <div className="profile-label">Ваша идея</div>
                  </div>
                  
                  {/* Правая часть: Результат с аналитикой */}
                  <div className="profile-right-pane">
                    <div className="pane-header">
                      <h3>Подобранный образ</h3>
                      <div className="color-indicator">
                        <span>Цветовая гамма:</span>
                        <div className="color-circle" style={{ backgroundColor: outfit.color }}></div>
                      </div>
                    </div>
                    
                    <div className="profile-items-row">
                      {outfit.items.map((item, i) => (
                        <div key={i} className="profile-result-item">
                           <img src={item.image_url} alt="clothing" />
                           <div className="item-stats">
                             <span className="stat-cat">{item.category}</span>
                             <span className="stat-sim">{item.similarity}% сходство</span>
                           </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
              {profileData.outfits.length === 0 && <p style={{textAlign:'center'}}>Вы еще ничего не сохранили.</p>}
            </div>
          </div>
        )}

        {/* ОБНОВЛЕННАЯ ЛЕНТА (С УМНЫМИ РЕКОМЕНДАЦИЯМИ) */}
        {view === 'feed' && (
          <div className="feed-container">
            <h2 className="feed-title">{token ? "Рекомендации для вас" : "Вдохновение от сообщества"}</h2>
            <div className="feed-grid">
              {feed.map((outfit) => (
                <div key={outfit.id} className={`feed-card ${outfit.is_recommended ? 'recommended-card' : ''}`}>
                  {outfit.is_recommended && <div className="rec-badge">✨ Подобрано для вас</div>}
                  <div className="combo-images">
                    {outfit.items.map((item, i) => (
                      <div key={i} className={`combo-item item-${i}`}>
                         <img src={item.image_url} alt="clothing" />
                      </div>
                    ))}
                  </div>
                  <div className="feed-card-footer">
                    <p><b>@{outfit.author_name}</b></p>
                    <button className="color-btn" onClick={() => fetchFeed(outfit.dominant_color)}>
                      Похожие по цвету 🎨
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;