# server.py
import socketio
from fastapi import FastAPI
from uuid import uuid4
from time import time

from models import MessagePayload, make_bot_reply, Message

# ────────── 1. Socket.IO объект ──────────
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",  # CORS для локальной разработки
    json=MessagePayload.model_json,  # чтобы SIO сериализовал так же, как Pydantic
)

# namespace /ml
ml_ns = "/ml"

# ────────── 2. FastAPI как оболочка над ASGI ──────────
app = FastAPI()
app.mount("/", socketio.ASGIApp(sio, socketio_path="socket.io"))


# ────────── 3. Обработчики событий ──────────
@sio.event(namespace=ml_ns)
async def connect(sid, environ):
    print(f"🔌  Клиент подключён: {sid}")


@sio.event(namespace=ml_ns)
async def disconnect(sid):
    print(f"❌  Клиент отключился: {sid}")


@sio.event(namespace=ml_ns)
async def message(sid, data):
    """
    data — это словарь, который соответствует модели MessagePayload.
    Socket.IO уже распарсил JSON ⇒ dict.
    """
    try:
        payload = MessagePayload.model_validate(data)
    except Exception as e:
        print("⚠️  Неверный payload:", e)
        return

    # 1. Сообщаем клиенту, что началась обработка
    await sio.emit("loading", namespace=ml_ns, to=sid)

    # 2. Запускаем ваш парсер
    reply_text = await run_parser(
        payload.message.content,
        payload.selectedList,
    )

    # 3. Отправляем готовый ответ
    reply: Message = make_bot_reply(reply_text)
    await sio.emit("message", reply.model_dump(), namespace=ml_ns, to=sid)


# ────────── 4. Заглушка парсера ──────────
async def run_parser(text: str, selected: list[str]) -> str:
    """
    Вставьте сюда свой код:
    • вызов Python‑парсера;
    • обращение к внешнему сервису;
    • запуск LLM‑клиента.
    """
    # демо‑ответ
    return f"Вы сказали: «{text}». Выбрано: {', '.join(selected)}"


# ────────── 5. Точка входа (uvicorn) ──────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=5500,
        reload=True,  # удобно в разработке
    )
