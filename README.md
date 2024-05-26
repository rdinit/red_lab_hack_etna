# RedLabHack, ETNA


## Запуск сервиса

- В корне репозитория создать папку `data` и положить файл с данным `metrics_collector.tsv.gz`

- Сборка образа
```shell
docker build -t etna-anomaly-detector .
```

- Запуск образа
```shell
docker run -p 8501:8501 etna-anomaly-detector
```

- Интерфейс сервиса в браузере
```shell
 http://0.0.0.0:8501
```

## Детектирование аномалий

1. Выбрать метрику
2. Выбрать временной интервал
3. Нажать кнопку "Search Anomalies"
