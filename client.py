import requests
import time
import hashlib
import re

BASE_URL = "http://127.0.0.1:8000"


def generate_hash(token: str, timestamp: str) -> str:
    return hashlib.sha256(f"{token}:{timestamp}".encode("utf-8")).hexdigest()


def send_request(method: str, endpoint: str, data=None, username=None, token=None):
    headers = {}
    if username and token:
        timestamp = str(int(time.time()))
        headers = {
            "X-Username": username,
            "X-Timestamp": timestamp,
            "X-Auth-Token": generate_hash(token, timestamp),
        }

    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "post":
            response = requests.post(url, json=data, headers=headers)
        elif method == "get":
            response = requests.get(url, headers=headers)
        else:
            raise ValueError("Неверный метод запроса.")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        detail = response.json().get("detail", str(e)) if response is not None else str(e)
        print(f"Ошибка ({response.status_code if response else 'нет ответа'}): {detail}")
        return None


def validate_password(password: str) -> str:
    if len(password) < 10:
        return "Пароль должен быть не менее 10 символов."
    if not any(char.isdigit() for char in password):
        return "Пароль должен содержать хотя бы одну цифру."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_-]", password):
        return "Пароль должен содержать хотя бы один спецсимвол."
    return ""


def get_valid_password() -> str:
    password = input("Введите пароль: ")
    error_message = validate_password(password)
    if error_message:
        print(f"Ошибка: {error_message}")
        return get_valid_password()

    confirm_password = input("Подтвердите пароль: ")
    if password != confirm_password:
        print("Ошибка: Пароли не совпадают.")
        return get_valid_password()

    return password


def register_user():
    username = input("Введите имя пользователя для регистрации: ")
    print("Требования к паролю:")
    print("- Пароль должен содержать не менее 10 символов.")
    print("- Пароль должен включать хотя бы одну цифру.")
    print("- Пароль должен содержать хотя бы один спецсимвол.")
    password = get_valid_password()

    data = {"username": username, "password": password}
    result = send_request("post", "/register", data)

    if result:
        print("Регистрация успешна.")
        return result.get("tech_token"), username
    return None, None


def login_user():
    username = input("Введите имя пользователя для входа: ")
    password = input("Введите пароль: ")
    data = {"username": username, "password": password}

    result = send_request("post", "/login", data)
    if result:
        print("Успешная авторизация.")
        return result.get("tech_token"), username
    else:
        print("Ошибка авторизации.")
        return None, None


def perform_sieve(limit, username, token):
    data = {"limit": limit}
    result = send_request("post", "/sieve", data, username, token)
    if result:
        primes = result.get("primes", [])
        count = result.get("count", 0)
        ascii_image = result.get("ascii_image", "")
        base64_image = result.get("base64_image", "")
        table_image_path = result.get("table_image_path", "")

        print(f"Простые числа до {limit}: {primes}")
        print(f"Найдено простых чисел: {count}")
        print("\nASCII изображение простых чисел:")
        print(ascii_image)
        print("\nBase64 изображение (первые 200 символов):")
        print(base64_image[:200], "...")
        print(f"\nПуть к таблице изображения: {table_image_path}")
    else:
        print("Ошибка при выполнении операции 'Решето Аткина'.")


def get_sieve_history(username, token):
    result = send_request("get", "/sieve/history", username=username, token=token)
    if result:
        if not result:
            print("История запросов отсутствует.")
        else:
            print("История запросов решета Аткина:")
            for record in result:
                print(f"Предел: {record['limit']}, Время: {record['timestamp']}")
    else:
        print("Ошибка при запросе истории решета.")


def main():
    print("Добро пожаловать в клиент решета Аткина!")
    token = None
    username = None

    while True:
        if not token:
            command = input("1 - Регистрация\n2 - Авторизация\n3 - Выход\nВыберите опцию: ").strip()
            if command == "1":
                token, username = register_user()
            elif command == "2":
                token, username = login_user()
            elif command == "3":
                print("Выход.")
                break
            else:
                print("Неверная команда.")
        else:
            command = input("1 - Выполнить решето Аткина\n2 - История запросов\n3 - Выйти\nВыберите опцию: ").strip()
            if command == "1":
                try:
                    limit = int(input("Введите предел для генерации простых чисел: "))
                    perform_sieve(limit, username, token)
                except ValueError:
                    print("Ошибка: Предел должен быть числом.")
            elif command == "2":
                get_sieve_history(username, token)
            elif command == "3":
                print("Выход.")
                break
            else:
                print("Неверная команда.")


if __name__ == "__main__":
    main()




















