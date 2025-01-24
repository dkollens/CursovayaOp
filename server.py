import json
import bcrypt
import re
import uuid
import hashlib
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List
from datetime import datetime
from PIL import Image, ImageDraw
import random
import base64
import pyfiglet
import colorama
from colorama import Fore, Style

app = FastAPI()
# uvicorn server:app --reload
# python client.py

def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

def load_history():
    try:
        with open('sieve_history.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_history(history):
    with open('sieve_history.json', 'w') as f:
        json.dump(history, f)

users = load_users()
sieve_history_records = load_history()

class User(BaseModel):
    username: str
    password: str

class SieveRequest(BaseModel):
    limit: int

def validate_password(password: str) -> bool:
    has_digit = any(char.isdigit() for char in password)
    has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>_-]", password))
    return has_digit and has_special

def generate_hash(token: str, timestamp: str) -> str:
    combined = f"{token}:{timestamp}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

@app.post("/register")
async def register(user: User):
    if user.username in users:
        raise HTTPException(status_code=409, detail="Пользователь уже существует.")
    if not validate_password(user.password):
        raise HTTPException(status_code=400, detail="Пароль должен содержать хотя бы одну цифру и один спецсимвол.")

    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    tech_token = str(uuid.uuid4())
    users[user.username] = {
        "hashed_password": hashed_password.decode('utf-8'),
        "tech_token": tech_token,
    }
    save_users(users)
    return {"message": "Регистрация прошла успешно.", "tech_token": tech_token}

@app.post("/login")
async def login(user: User):
    if user.username not in users:
        raise HTTPException(status_code=400, detail="Пользователь не обнаружен.")

    stored_user = users[user.username]
    if not bcrypt.checkpw(user.password.encode('utf-8'), stored_user["hashed_password"].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Неправильный пароль.")

    return {"message": "Успешная авторизация!", "tech_token": stored_user["tech_token"]}

@app.post("/sieve")
async def sieve(sieve_request: SieveRequest, request: Request):
    timestamp = request.headers.get("X-Timestamp")
    token_hash = request.headers.get("X-Auth-Token")
    username = request.headers.get("X-Username")

    if not timestamp or not token_hash or not username:
        raise HTTPException(status_code=401, detail="Не хватает авторизационных данных.")

    user = users.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не существует.")

    expected_hash = generate_hash(user["tech_token"], timestamp)
    if token_hash != expected_hash:
        for offset in [-1, 1, -2, 2]:
            timestamp_offset = str(int(timestamp) + offset)
            if token_hash == generate_hash(user["tech_token"], timestamp_offset):
                break
        else:
            raise HTTPException(status_code=401, detail="Неверный токен авторизации.")

    limit = sieve_request.limit
    if limit < 2:
        raise HTTPException(status_code=400, detail="Предел должен быть больше 1.")

    primes, prime_img_path, base64_image, table_img_path, ascii_art = sieve_of_atkin(limit)

    sieve_history_records.append({"limit": limit, "timestamp": datetime.now().isoformat()})
    save_history(sieve_history_records)

    return {
        "primes": primes,
        "count": len(primes),
        "ascii_image": ascii_art,
        "base64_image": base64_image,
        "table_image_path": table_img_path,
    }

@app.get("/sieve/history", response_model=List[dict])
async def get_sieve_history():
    if not sieve_history_records:
        raise HTTPException(status_code=404, detail="Нет истории запросов.")
    return sieve_history_records

# Решето Аткина

def sieve_of_atkin(limit):
    sieve = [False] * (limit + 1)
    primes = []

    if limit >= 2:
        primes.append(2)
    if limit >= 3:
        primes.append(3)

    for x in range(1, int(limit ** 0.5) + 1):
        for y in range(1, int(limit ** 0.5) + 1):
            n = (4 * x ** 2) + (y ** 2)
            if n <= limit and (n % 12 == 1 or n % 12 == 5):
                sieve[n] = not sieve[n]

            n = (3 * x ** 2) + (y ** 2)
            if n <= limit and n % 12 == 7:
                sieve[n] = not sieve[n]

            n = (3 * x ** 2) - (y ** 2)
            if x > y and n <= limit and n % 12 == 11:
                sieve[n] = not sieve[n]

    for p in range(5, int(limit ** 0.5) + 1):
        if sieve[p]:
            for k in range(p ** 2, limit + 1, p ** 2):
                sieve[k] = False

    for p in range(5, limit + 1):
        if sieve[p]:
            primes.append(p)

    img_path = create_image(primes, limit)
    base64_image = convert_to_base64(img_path)
    table_image_path = create_table_image(primes, limit)
    ascii_table =  create_ascii_table(primes, limit)

    return primes, img_path, base64_image, table_image_path, ascii_table

# Генерация PNG изображения

def create_image(primes, limit):
    width = 1000
    height = 1000
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    for p in primes:
        x, y = p % width, p // width
        if y < height:
            draw.point((x, y), fill=0)

    img_path = f"primes_up_to_{limit}.png"
    img.save(img_path)
    return img_path

# Конвертация изображения в Base64

def convert_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# Генерация таблицы с простыми числами

def create_table_image(primes, limit):
    size = int(limit ** 0.5) + 1
    img = Image.new("RGB", (size * 20, size * 20), "white")
    draw = ImageDraw.Draw(img)

    for i in range(limit + 1):
        x, y = (i % size) * 20, (i // size) * 20
        color = "blue" if i in primes else "white"
        draw.rectangle([x, y, x + 20, y + 20], fill=color, outline="black")
        draw.text((x + 5, y + 5), str(i), fill="black")

    img_path = f"table_primes_up_to_{limit}.png"
    img.save(img_path)
    img.show()
    return img_path

# Генерация ASCII
def create_ascii_table(primes, limit):
    colorama.init(autoreset=True)
    size = int(limit ** 0.5) + 1
    ascii_table = []
    top_border = "┌" + "┬".join(["───"] * size) + "┐"
    ascii_table.append(top_border)

    for row in range(size):
        line = []
        for col in range(size):
            number = row * size + col
            if number > limit:
                line.append("   ")
            elif number in primes:
                line.append(Fore.RED + f"{number:3}" + Style.RESET_ALL)
            else:
                line.append(f"{number:3}")
        ascii_table.append("│" + "│".join(line) + "│")
        if row < size - 1:
            ascii_table.append("├" + "┼".join(["───"] * size) + "┤")

    bottom_border = "└" + "┴".join(["───"] * size) + "┘"
    ascii_table.append(bottom_border)
    ascii_art = "\n".join(ascii_table)
    return ascii_art


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)



















