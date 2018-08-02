# Touchdesigner 🙌 Firebase

## Запускаем python-скрипт для передачи firebase в osc

1. Установить python 3.6

**В macOs**. Ничего делать не надо. Python 3.6 уже установлен

**В Windows**. https://www.python.org/downloads/release/python-366/


2. Установить pyenv

**В macOs**. В консоли: `$ brew install pipenv`

**В Windows**. В консоли: `$ pip install --user pipenv`

Подробнее — https://docs.pipenv.org/


3. Запускаем скрипт

Заходим в консоли а папку со скачанным скриптом (это папка python в репозитории). Выполняем: `pipenv run python firebase-osc.py`


Должны появится строчки, начинающияся с `<<< Firebase in:` и `>>> Osc out:`
