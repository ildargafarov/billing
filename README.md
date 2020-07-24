# Changelog

[Unreleased]

Added

- Добавил возможность параллельной обработки транзакции через несколько очередей и нескольких воркеров.
Решение в какую очередь отправить транзакцию принимается на основе формулы `hash(credit_account_id) % queue_count` получается, 
что все транзакции по одному аккаунту всегда попадают в одну очередь. Таким образом, мы сохраняем очередность транзакции для одного аккаунта и распараллеливаем обработку нескольких транзакции.
- Исправил имена полей `create_date`, `customer_id` в ответе на запрос `GET /api/v1/billing/accounts/{account_id}/operations`.
- Добавил валидацию значения `amount`

# Архитектура

## Выделим основные требования из задания, влияющие на архитектуру системы:

- `CNR1` Клиенты совершают большое количество транзакции.
- `CNR2` Нужно обеспечить высокую производительность АПИ.
- `CNR3` Данные должны быть консистентными в любой момент времени.
- `CNR4` Одна валюта USD.
- `CNR5` Клиент имеет один кошелек.
- `CNR6` Сохраняется информация о кошельке и остатке средств на нем.
- `CNR7` Сохраняется информация о всех операциях на кошельке клиента.
- `CNR8` Апи содержит операции:
   - создание клиента с кошельком
   - зачисление денежных средств на кошелек клиента
   - перевод денежных средств с одного кошелька на другой

## Сделаем некоторые выводы по требованиям:

- `CNC1` Из `CNR1` и `CNR2` можно сделать предположение, что `запросов на изменения данных в систему больше,
чем запросов на чтение и что система должна уметь обрабатывать эти изменения очень быстро и много`.
Также в `CNR8` описаны только методы для создания транзакции, но нет методов для чтения данных, что усиливает
наше предположение, которое уже можно сформулировать в заключение: `для клиента важно провести транзакцию,
нежели получить текущий баланс кошелька или операции по нему`.
- `CNC2` Из `CNR3` - консистентность данных состоит из двух частей:
    - Актуальность данных - означает, что запросы на чтение должны выдавать данные в актуальном состоянии.
    - Целостность - данные должны быть непротиворечивыми.
Но `CNC1` говорит, что клиенту не очень важен баланс кошелька, либо важен, но не срочно,
значит `мы можем пренебречь актуальностью данных, но не целостностью`
- `CNC2` Из `CNR6` и `CNR7` - `обязательно нужно хранить в БД баланс кошелька и операции по нему`


## Описание архитектуры

Обработка запроса клиента включает в себя следующие действия: 
- заблокировать счета
- нужно получить текущий баланс по счетам
- проверить, что средств на счете достаточно
- добавить транзакцию
- изменить баланс на счетах
- разблокировать счета
    
Все эти действия происходят в единой транзакции. 

Рассмотрим такую ситуацию:
1. Имеется счет на котором лежит какая-то сумма денег. 
2. Поступает запрос от Клиента 1, который хочет снять с этого счета немного денег. 
3. В то же время другой Клиент 2 хочет положить на этот счет какую то сумму денег.
По нашему алгоритму, Клиенту 2 придется подождать, пока Клиент 1 закончит свою операцию. Но это несправедливо! 
В любом случае операция "положить на счет" никак не зависит от других операции по счету и от кол-ва денег.
Возможно Клиент 2 очень быстрый и совершает много операции, но почему он должен ждать, когда ждать не имеет смысла.

Мы из требований сделали вывод, что клиенту не очень важно знать актуальное состояние его счетов. Мы  исключили это 
свойство из определения консистентности. Мы можем заявить клиенту, что гарантируем, что данные будут непротиворечивыми, 
но не гарантируем, что они будут актуальные какое-то время T. При поступлении запроса от клиента, мы запомним операцию, 
которую он хочет совершить и пообещаем выполнить ее в течение времени T.  

Чтобы проделать это, заведем очередь, куда будем складывать все запросы от клиента. Клиент не ждет пока мы обработаем запрос, 
мы ему отвечаем как только сохранили запрос. На другом конце очереди будет находиться обработчик, который поочередно будет 
доставать запрос и обрабатывать его. После обработки запроса, состояние счетов меняется. 

Такой подход имеет много плюсов:
- мы отделили задачи принятия запроса от ее обработки. Клиент не зависит от загруженности системы в данный момент.
Мы можем принять сколько угодно сообщений и отложить их обработку.
- если мы упремся в производительность, то наверняка есть способы разделить одну очередь на несколько. Например, могут быть 
транзакции счета которых вообще не связаны, их необязательно обрабатывать последовательно, мы можем положить их в разные очереди.
- желательно, чтобы очередь обрабатывал один воркер, если обработчиков несколько, то порядок транзакции может быть нарушен 
(если например воркер взял задачу и упал, в это время другой воркер взял следующую задачу, первый воркер восстановился и 
обработал первую задачу тогда получилось, что порядок задач изменился, а для транзакции это критично). Но как и в примере, 
мы можем одному воркеру отдавать транзакции, на пополнение счета, а другому воркеру на перемещение денег, т.к. мы в примере выяснили,
 что пополнение не от чего не зависит (скорее всего здесь есть тонкости и я не совсем прав).
- очередь выравнивает нагрузку: когда запросов много, они накапливаются, когда мало, очередь уменьшается. Но воркеры всегда будут загружены полностью.

Недостатки:
- возможно клиенту критично знать актуальное состояние счетов для принятия решения. Одно из решений, клиент сам у себя ведет 
подсчет своих денег на счетах. Он же знает, сколько и кому он отправил.

## Реализация

При запуске разворачиваются 4 контейнера:
- `pg` - Postgresql основная БД
- `api` - Http Api
- `rabbitmq` - очередь сообщений
- `worker` - celery воркер

## Что можно улучшить

- сейчас информация по счетам запрашивается из той же базы, где и хранятся счета и транзакции, мы можем убрать нагрузку на чтение с этой БД,
заведя новую базу для кэша, например Redis. Синхронизировать состояние можно разными способами. Например в редисе и в основной БД можно завести счетчики, которе показывают актуальность данных.
Как только воркер обновил состояние счета, он также инкрементирует счетчик в основной БД. При запросе на чтение, кэш сравнивает счетчики и синхронизирует состояние.
Либо можно сделать так, чтобы воркер удалял запись из кеша при изменении состояния.


# API

## `POST /api/v1/billing/customers`

Создает клиента и привязывает ему счет.

### Пример ответа
```
{
    "accountId": "2:current",
    "customerId": 2
}
```

## `GET /api/v1/billing/customers`

Получить список всех клиентов.

### Пример ответа

```
[
    {
        "id": 1,
        "registerDate": "2020-07-20T12:54:54.591382"
    },
    {
        "id": 2,
        "registerDate": "2020-07-20T12:54:55.528643"
    }
]
```

## `GET /api/v1/billing/customers/{customer_id}/accounts`

Получить все счета клиента.

## Параметры
- `customer_id` - id клиента

## Ошибки
- `404 Not Found` - клиент не найден

### Пример ответа

```
[
    {
        "customerId": 1,
        "id": "1:current",
        "balance": 0.0,
        "createDate": "2020-07-20T12:54:54.620675"
    }
]
```

## `POST /api/v1/billing/txn`

Запланировать транзакцию.

## Тело запроса
```
{
    "amount": 1000,
    "creditAccountId": "1:current",
    "debitAccountId": "2:current"
}
```
- `amount` - сумма транзакции
- `creditAccountId` - счет откуда  списываются деньги. Если `null` или поле вообще отсутствует, то считается, что это просто
   транзакция на зачисление на счет
- `debitAccountId` - счет куда поступают деньги

## Ошибки
- `400 Bad Request` - отсутсвуют нужные поля

Воркер проверяет:
- наличие таких счетов
- что на счету достаточно средств

### Пример ответа

```
{
    "status": "ok"
}
```


## `GET /api/v1/billing/accounts/{account_id}/operations`

Получить список операции на счету клиента.

## Параметры
- `account_id` - id счета

## Ошибки
- `404 Not Found` - счет не найден

### Пример ответа

```
{
    "accountId": "2:current",
    "balance": 15489.59,
    "create_date": "2020-07-20T08:49:41.758424",
    "customer_id": 2,
    "operations": [
        {
            "amount": 6454.33,
            "balance": 15489.59,
            "date": "2020-07-20T08:52:30.124019"
        },
        {
            "amount": -1275.24,
            "balance": 9035.26,
            "date": "2020-07-20T08:52:19.818571"
        },
        {
            "amount": 643.5,
            "balance": 10310.5,
            "date": "2020-07-20T08:51:57.962655"
        },
        {
            "amount": -456.0,
            "balance": 9667.0,
            "date": "2020-07-20T08:51:48.214376"
        },
        {
            "amount": 123.0,
            "balance": 10123.0,
            "date": "2020-07-20T08:51:40.110065"
        },
        {
            "amount": 10000.0,
            "balance": 10000.0,
            "date": "2020-07-20T08:51:27.441993"
        }
    ]
}
```

# Запуск

```
$ docker-compose up
```
