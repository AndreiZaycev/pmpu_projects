Проект #2  
Данный проект содержит логику прасинга телеграм каналов с упоминаниями СПбГУ и МГУ и агрегацией различных статистик. Робот будет собирать по всем чатам с кол-вом подпищиков > 100 все упоминания об СПбГУ и МГУ и складывать их в crawled_messages.csv. Статистики будут посчитаны в universities_posts_stats.csv и также будут выведены в консоль. И также будет выведен график publications_count.png. 

Для того чтобы запустить проект, выполните последовательно: 
```
git clone <this project>
```
После этого устанавливаем зависимости 
```
pip install -r requirements.txt
```
И запускаем парсинг 
```
python universities_crawler.py
```
Параметры cli
```
options:
  -h, --help            show this help message and exit
  --api-id API_ID       Telegram API ID
  --api-hash API_HASH   Telegram API Hash
  --limit LIMIT         Лимит сообщений для анализа (по умолчанию: 10000)
  --min-participants-count MIN_PARTICIPANTS_COUNT
                        Минимальное кол-во подписчиков для парсинга канала
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Уровень логирования (по умолчанию: INFO)
```


Предварительно перед запуском вам нужно получить access_tokens для телеграма на сайте https://my.telegram.org/auth и прокинуть в переменные окружения
``` 
TELEGRAM_API_ID
TELEGRAM_API_HASH
```

После запуска Вам потребуется авторизоваться по номеру телефона и паролю в вашем телеграм аккаунте.  
Чтобы запустить тесты, достаточно запустить команду 
```
pytest -v test.py
``` 

