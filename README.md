# Тестирование

### Общее описание
Тестироование 2-х небольших Django проектов. Тестирование выполнено при помощи
UnitTest и pytest.

### Подготовка к запуску под Linux
* клонируем репозиторий на ПК
  ```
  git clone git@github.com:PetrovKRS/Testing_in_Django.git
  ```
* переходим в рабочую папку склонированного проекта
* разворачиваем виртуальное окружение
  ```
  python3 -m venv venv
  ```
  ```
  source venv/bin/activate
  ```
* устанавливаем зависимости из файла requirements.txt
  ```
  pip install --upgrade pip
  ```
  ```
  pip install -r requirements.txt
  ```
### Запуск тестирования
* запускаем тестирование
  ```
  bash run_tests.sh
  ```

Стек технологий: |*| Python 3.9 |*| Unittest |*| PyTest |*|
