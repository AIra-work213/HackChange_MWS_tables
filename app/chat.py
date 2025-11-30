import streamlit as st
import requests
import uuid

# Конфигурация
API_URL = "http://localhost:8000/"

st.set_page_config(
    page_title="Чат-бот для анализа постов",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Чат-бот для анализа постов")
st.markdown("Задайте вопрос о постах, и я найду нужную информацию в базе данных.")

# Инициализация session_id для уникальной сессии пользователя
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Инициализация истории чата
if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение истории чата
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода
if prompt := st.chat_input("Введите ваш вопрос..."):
    # Добавляем сообщение пользователя
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Отправляем запрос к серверу
    with st.chat_message("assistant"):
        with st.spinner("Думаю... (это может занять несколько минут)"):
            try:
                response = requests.get(
                    API_URL,
                    json={
                        "query": prompt,
                        "session_id": st.session_state.session_id
                    },
                    timeout=None  # Без ограничения времени - ждём до конца
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("response", "Не удалось получить ответ")
                else:
                    answer = f"Ошибка сервера: {response.status_code}"
                    
            except requests.exceptions.ConnectionError:
                answer = "❌ Не удалось подключиться к серверу. Убедитесь, что сервер запущен."
            except Exception as e:
                answer = f"❌ Ошибка: {str(e)}"
        
        st.markdown(answer)
    
    # Добавляем ответ ассистента в историю
    st.session_state.messages.append({"role": "assistant", "content": answer})

# Боковая панель с информацией
with st.sidebar:
    st.header("ℹ️ Информация")
    st.markdown("""
    ### Примеры запросов:
    - Покажи топ-5 постов по лайкам
    - Найди посты с высокой эффективностью
    - Покажи посты за понедельник
    - Какие посты имеют больше 100 просмотров?
    
    ### 💡 Подсказка:
    Бот помнит контекст диалога! Вы можете задавать уточняющие вопросы:
    - "Покажи топ-5 постов по лайкам"
    - "А теперь покажи их тексты"
    - "Отсортируй по просмотрам"
    
    ### Доступные поля:
    - `post_id` - ID поста
    - `title` - Заголовок
    - `text` - Текст поста
    - `views` - Просмотры
    - `likes` - Лайки
    - `reposts` - Репосты
    - `comments_count` - Кол-во комментов
    - `ER` - Engagement Rate
    - `Efficiency` - Эффективность
    - `day_of_week` - День недели
    - `time_period` - Время суток
    """)
    
    st.divider()
    
    if st.button("🗑️ Очистить историю"):
        # Очищаем историю на сервере
        try:
            requests.post(
                f"{API_URL}clear",
                json={"session_id": st.session_state.session_id},
                timeout=10
            )
        except:
            pass
        # Очищаем локальную историю
        st.session_state.messages = []
        # Создаём новый session_id
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
    
    st.caption(f"Session ID: `{st.session_state.session_id[:8]}...`")
