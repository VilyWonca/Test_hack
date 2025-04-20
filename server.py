# server.py
import socketio
from uuid import uuid4
from time import time
from typing import Literal

from pydantic import BaseModel

from main import main as run_main  # импорт твоей главной функции

# ────────── Pydantic-модели ──────────

MessageRole = Literal["user", "bot"]

class Message(BaseModel):
    id: str
    role: MessageRole
    content: str
    timestamp: int

class MessagePayload(BaseModel):
    message: Message
    selectedList: list[str]  # это и есть snippets

def make_bot_reply(text: str) -> Message:
    return Message(
        id=str(uuid4()),
        role="bot",
        content=text,
        timestamp=int(time() * 1000)
    )

# ────────── Socket.IO сервер ──────────

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)
app = socketio.ASGIApp(sio, socketio_path="socket.io")
ml_namespace = "/ml"

@sio.event(namespace=ml_namespace)
async def connect(sid, environ):
    print(f"🔌 Клиент подключён: {sid}")

@sio.event(namespace=ml_namespace)
async def disconnect(sid):
    print(f"❌ Клиент отключился: {sid}")

@sio.event(namespace=ml_namespace)
async def message(sid, data: dict):
    try:
        # 🔎 Валидация структуры запроса
        payload = MessagePayload.model_validate(data)
        user_command = payload.message.content
        snippets = payload.selectedList

        print(f"[📥] Команда: {user_command}")
        print(f"[📄] Сниппеты: {snippets}")

        # 🌀 Отправляем клиенту "loading"
        await sio.emit("loading", namespace=ml_namespace, to=sid)

        # 🚀 Запускаем главный пайплайн
        explanation = run_main(user_command=user_command, snippets=snippets)

        # 📤 Отправляем успешный ответ
        reply = make_bot_reply(explanation)
        await sio.emit("message", explanation, namespace=ml_namespace, to=sid)


    except Exception as e:
        print(f"❌ Ошибка при обработке: {e}")
        reply = make_bot_reply(f"⚠️ Ошибка: {str(e)}")
        await sio.emit("message", explanation, namespace=ml_namespace, to=sid)


# ────────── Запуск ──────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5500)
