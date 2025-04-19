# Итоговый проект «Фудграм»

«Фудграм» — сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

Рецепты приведенные в данном проекте являются вымышленными. Список игридиентов и прочая информация недостоверны. 

## Запуск проекта:

**1. Клонировать репозиторий**:

```
https://github.com/LackOfHapinesS/foodgram-st.git
```

**2. Перейти в директорию backend\foodgram:**

```
cd .\backend\foodgram
```

**3. Создать файл .env и заполнить его:**

```
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
USE_SQLITE=False
DB_ENGINE=django.db.backends.postgresql
DB_NAME=foodgram
DB_USER=foodgram_user
DB_PASSWORD=foodgram_password
DB_HOST=postgres
DB_PORT=5432
```

**4. Перейти в директорию infra и поднять контейнеры:**

```
cd ..\infra
```

```
docker-compose up -d
```

## Список контейнеров:

 - foodgram-front — контейнер с фронтенд-приложением.

 - foodgram-db — контейнер c БД.

 - foodgram-backend — контейнер с бизнес-логикой и API.

 - foodgram-proxy — контейнер с обратным прокси-сервером.


## Изначально существующие учетные записи:

 - **admin**

    Почта: admin@gmail.com

    Пароль: Pineapple34
        
 - **egot_cherevichkin**

    Почта: egorka2003@gmail.com

    Пароль: TheBigBoomTherory78

 - **oleg_porenko**

    Почта: olegrulit6@gmail.com

    Пароль: IloveChilliconCarne

 - **lavanda_chuvstvuet**

    Почта: lavander0@gmail.com

    Пароль: Wag1RonWisley


## Об авторе:
Студент 4 курса ТПУ ИШИТР Попов С.Д.