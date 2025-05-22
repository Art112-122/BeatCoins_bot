# 🤖 Крипто-Бот Асистент

Telegram-бот для моніторингу цін криптовалют у реальному часі з TradingView-графіками, кастомними лімітами та push-повідомленнями. Працює з базою MySQL та API Binance.

## 📆 Можливості

* 📈 Перегляд графіків TradingView прямо в Telegram
* 💰 Перевірка актуального курсу монети
* ⚙ Задання монети та лімітів сповіщень (верхній / нижній)
* 🔔 Автоматичне повідомлення про пробиття лімітів
* ⏸ Вмикання / вимикання сповіщень
* 📡 Інтеграція з Binance API для отримання курсу
* 💄 Зберігання даних у MySQL

## 🧹 Стек технологій

* Python 3.10+
* [Aiogram 3](https://docs.aiogram.dev/)
* aiomysql
* asyncio
* dotenv
* TradingView (WebApp)
* Binance API

## 📁 Структура проєкту

```
├── bot/
│   └── state.py              # FSM стани
├── db/
│   └── connection.py         # Підключення до MySQL
├── api/
│   └── api.py                # Отримання ціни з Binance
├── main.py                   # Основна логіка бота
├── .env                      # Секрети: токен бота, URL WebApp
└── README.md
```

## ⚙ Налаштування

### 1. Клонуйте репозиторій:

```bash
git clone https://github.com/yourusername/crypto-assistant-bot.git
cd crypto-assistant-bot
```

### 2. Встановіть залежності:

```bash
pip install -r requirements.txt
```

> Якщо `requirements.txt` відсутній, створіть його самостійно з:

```bash
pip freeze > requirements.txt
```

### 3. Створіть `.env` файл:

```env
BOT_TOKEN=ваш_telegram_bot_token
WEB_APP=https://ваш_веб_додаток_з_графіком
```

### 4. Налаштуйте базу MySQL

```sql
CREATE DATABASE crypto_bot;

USE crypto_bot;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    name VARCHAR(255),
    token VARCHAR(20) DEFAULT 'BTCUSDT',
    low_limit INT DEFAULT NULL,
    high_limit INT DEFAULT NULL,
    notices BOOLEAN DEFAULT TRUE
);
```

### 5. Запуск

```bash
python main.py
```

> Скрипт автоматично створює таблиці, якщо потрібно ("create\_tables")

---

## 🔐 Безпека

* Уникайте коміту `.env` в репозиторій
* Рекомендується запуск через Docker або systemd у production

---

## 🚀 Плани на майбутнє

* Підтримка мультивалютних графіків одночасно
* Зберігання історії сповіщень
* Адмін-панель у WebApp
* Обробка виключень через middleware

---

## 📬 Контакти

Маєш ідеї, баги або хочеш допомогти? Напиши [сюди](https://t.me/yourusername)
