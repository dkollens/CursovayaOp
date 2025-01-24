import unittest
import requests
import time
import hashlib

BASE_URL = "http://127.0.0.1:8000"


class TestServerClientIntegration(unittest.TestCase):

    def generate_hash(self, token, timestamp):
        return hashlib.sha256(f"{token}:{timestamp}".encode("utf-8")).hexdigest()

    def setUp(self):
        self.username = "test_user_" + str(int(time.time()))
        self.password = "ValidPassword123!"

    def test_register_user(self):
        data = {
            "username": self.username,
            "password": self.password
        }
        response = requests.post(f"{BASE_URL}/register", json=data)
        if response.status_code == 409:  # Пользователь уже существует
            self.skipTest("Пользователь уже существует, пропуск теста регистрации.")
        self.assertEqual(response.status_code, 200, f"Ожидался код 200, получен {response.status_code}")
        self.assertIn("tech_token", response.json(), "Отсутствует 'tech_token' в ответе")
        print(f"[SUCCESS] Регистрация пользователя {self.username} прошла успешно.")

    def test_login_user(self):
        # Регистрация пользователя перед тестом
        requests.post(f"{BASE_URL}/register", json={"username": self.username, "password": self.password})

        data = {
            "username": self.username,
            "password": self.password
        }
        response = requests.post(f"{BASE_URL}/login", json=data)
        self.assertEqual(response.status_code, 200, f"Ожидался код 200, получен {response.status_code}")
        self.assertIn("tech_token", response.json(), "Отсутствует 'tech_token' в ответе")
        self.tech_token = response.json().get("tech_token")
        print(f"[SUCCESS] Авторизация пользователя {self.username} прошла успешно.")

    def test_sieve_request(self):
        # Авторизация пользователя
        requests.post(f"{BASE_URL}/register", json={"username": self.username, "password": self.password})
        login_response = requests.post(f"{BASE_URL}/login", json={"username": self.username, "password": self.password})
        self.assertEqual(login_response.status_code, 200, f"Ожидался код 200, получен {login_response.status_code}")
        tech_token = login_response.json().get("tech_token")

        # Выполнение запроса "Решето Аткина"
        timestamp = str(int(time.time()))
        headers = {
            "X-Username": self.username,
            "X-Timestamp": timestamp,
            "X-Auth-Token": self.generate_hash(tech_token, timestamp),
        }
        sieve_data = {"limit": 35}
        response = requests.post(f"{BASE_URL}/sieve", json=sieve_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Ожидался код 200, получен {response.status_code}")
        self.assertIn("primes", response.json(), "Отсутствует 'primes' в ответе")
        print(
            f"[SUCCESS] Запрос 'Решето Аткина' с пределом 35 выполнен успешно. Простые числа: {response.json().get('primes', [])}")

    def test_invalid_sieve_limit(self):
        # Авторизация
        requests.post(f"{BASE_URL}/register", json={"username": self.username, "password": self.password})
        login_response = requests.post(f"{BASE_URL}/login", json={"username": self.username, "password": self.password})
        self.assertEqual(login_response.status_code, 200, f"Ожидался код 200, получен {login_response.status_code}")
        tech_token = login_response.json().get("tech_token")

        # Запрос с некорректным пределом
        timestamp = str(int(time.time()))
        headers = {
            "X-Username": self.username,
            "X-Timestamp": timestamp,
            "X-Auth-Token": self.generate_hash(tech_token, timestamp),
        }
        response = requests.post(f"{BASE_URL}/sieve", json={"limit": 1}, headers=headers)
        self.assertEqual(response.status_code, 400, f"Ожидался код 400, получен {response.status_code}")
        self.assertIn("detail", response.json(), "Отсутствует поле 'detail' в ответе")
        self.assertEqual(response.json()["detail"], "Предел должен быть больше 1.", "Неверное сообщение об ошибке")
        print("[SUCCESS] Проверка некорректного предела для 'Решета Аткина' успешно выполнена.")

    def test_invalid_auth_headers(self):
        # Некорректные заголовки авторизации
        headers = {
            "X-Username": self.username,
            "X-Timestamp": "invalid_timestamp",
            "X-Auth-Token": "invalid_token",
        }
        response = requests.post(f"{BASE_URL}/sieve", json={"limit": 50}, headers=headers)
        self.assertEqual(response.status_code, 401, f"Ожидался код 401, получен {response.status_code}")
        self.assertIn("detail", response.json(), "Отсутствует поле 'detail' в ответе")
        self.assertEqual(response.json()["detail"], "Пользователь не существует.", "Неверное сообщение об ошибке")
        print("[SUCCESS] Проверка некорректных заголовков авторизации успешно выполнена.")

    def test_sieve_history(self):
        # Авторизация пользователя
        requests.post(f"{BASE_URL}/register", json={"username": self.username, "password": self.password})
        login_response = requests.post(f"{BASE_URL}/login", json={"username": self.username, "password": self.password})
        self.assertEqual(login_response.status_code, 200, f"Ожидался код 200, получен {login_response.status_code}")
        tech_token = login_response.json().get("tech_token")

        # Запрос истории
        timestamp = str(int(time.time()))
        headers = {
            "X-Username": self.username,
            "X-Timestamp": timestamp,
            "X-Auth-Token": self.generate_hash(tech_token, timestamp),
        }
        response = requests.get(f"{BASE_URL}/sieve/history", headers=headers)
        self.assertEqual(response.status_code, 200, f"Ожидался код 200, получен {response.status_code}")
        self.assertIsInstance(response.json(), list, "Ожидался список в ответе")
        print(f"[SUCCESS] История запросов успешно получена: {response.json()}")


if __name__ == "__main__":
    unittest.main(verbosity=2)



