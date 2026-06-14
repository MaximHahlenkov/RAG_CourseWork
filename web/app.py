import chainlit as cl
import requests
import os
import uuid

API_URL = os.getenv("API_URL", "http://api:8000/api/v1")


def get_user_id():
    if not cl.user_session.get("user_id"):
        new_id = int(uuid.uuid4().int % 1000000)
        cl.user_session.set("user_id", new_id)
    return cl.user_session.get("user_id")


@cl.on_chat_start
async def start():
    user_id = get_user_id()

    actions = [
        cl.Action(name="list_files", payload={"value": "list"}, label="Мои документы"),
        cl.Action(name="clear_base", payload={"value": "clear"}, label="Очистить всё")
    ]

    await cl.Message(
        content=f"Добро пожаловать! Твой временный ID: `{user_id}`. \n\nЯ готов анализировать твои PDF/Docx/txt/MD. Просто прикрепи их к сообщению.",
        actions=actions
    ).send()


@cl.action_callback("list_files")
async def on_list_files(action):
    user_id = get_user_id()
    try:
        res = requests.get(f"{API_URL}/knowledge/files/{user_id}", timeout=10)
        if res.status_code == 200:
            files = res.json().get("files", [])
            if not files:
                await cl.Message(content="Твоя база знаний пока пуста.").send()
            else:
                files_str = "\n".join([f"- {f}" for f in files])
                await cl.Message(content=f"**Загруженные документы:**\n{files_str}").send()
    except Exception as e:
        await cl.Message(content=f"Ошибка при получении списка: {e}").send()


@cl.action_callback("clear_base")
async def on_clear_base(action):
    user_id = get_user_id()
    try:
        res = requests.delete(f"{API_URL}/knowledge/clear/{user_id}", timeout=10)
        if res.status_code == 200:
            await cl.Message(content="Твоя персональная база знаний успешно очищена!").send()
        else:
            await cl.Message(content="Не удалось очистить данные на сервере.").send()
    except Exception as e:
        await cl.Message(content=f"Ошибка связи: {e}").send()


@cl.on_message
async def main(message: cl.Message):
    user_id = get_user_id()

    if message.elements:
        for element in message.elements:
            if element.name.lower().endswith((".pdf", ".docx", ".doc", ".txt")):
                msg = cl.Message(content=f"Обработка `{element.name}`...")
                await msg.send()

                with open(element.path, "rb") as f:
                    files = {"file": (element.name, f, "application/pdf")}
                    res = requests.post(f"{API_URL}/knowledge/upload?user_id={user_id}", files=files)

                if res.status_code == 200:
                    msg.content = f"Документ `{element.name}` проиндексирован."
                else:
                    msg.content = f"Ошибка: {res.status_code}"
                await msg.update()
        return

    if message.content:
        msg = cl.Message(content="")
        await msg.send()

        payload = {"user_id": user_id, "query": message.content}
        try:
            res = requests.post(f"{API_URL}/chat/ask", json=payload, timeout=120)
            if res.status_code == 200:
                msg.content = res.json().get("answer", "Нет ответа.")
            else:
                msg.content = f"Ошибка API: {res.status_code}"
        except Exception as e:
            msg.content = f"Ошибка связи: {e}"

        await msg.update()