# Деплой в Яндекс.Облако (Compute Cloud VM)

MVP разворачивается на одной виртуальной машине тем же `docker-compose.yml`,
что используется локально — отдельный LB не нужен (см. README, "без Redis и LB").

## 0. Предварительные требования

- Установлен и авторизован [Yandex Cloud CLI](https://yandex.cloud/ru/docs/cli/quickstart) (`yc init`)
- Есть SSH-ключ (`~/.ssh/id_rsa.pub` или свой)
- Известен `folder-id`, в котором создаём ресурсы (`yc config get folder-id`)

## 1. Security group

Открываем только 22 (SSH), 80 (HTTP) и 443 (HTTPS, под будущий TLS). Порты БД и backend
наружу не открываются — в `docker-compose.yml` они уже забинжены на `127.0.0.1`.

```bash
yc vpc security-group create \
  --name shortener-sg \
  --network-name default \
  --rule "direction=ingress,port=22,protocol=tcp,v4-cidrs=[0.0.0.0/0]" \
  --rule "direction=ingress,port=80,protocol=tcp,v4-cidrs=[0.0.0.0/0]" \
  --rule "direction=ingress,port=443,protocol=tcp,v4-cidrs=[0.0.0.0/0]" \
  --rule "direction=egress,port=any,protocol=any,v4-cidrs=[0.0.0.0/0]"
```

Если сети `default` ещё нет — сначала `yc vpc network create --name default` и
`yc vpc subnet create --name default-ru-central1-a --zone ru-central1-a --network-name default --range 10.0.0.0/24`.

## 2. Создание ВМ

`cloud-init.yaml` из этого репозитория (`deploy/yandex-cloud/cloud-init.yaml`) ставит Docker
и docker compose plugin при первом старте.

```bash
yc compute instance create \
  --name shortener-vm \
  --zone ru-central1-a \
  --network-interface subnet-name=default-ru-central1-a,nat-ip-version=ipv4,security-group-ids=<SG_ID> \
  --create-boot-disk image-family=ubuntu-2204-lts,size=20 \
  --memory=2 --cores=2 \
  --ssh-key ~/.ssh/id_rsa.pub \
  --metadata-from-file user-data=deploy/yandex-cloud/cloud-init.yaml
```

`<SG_ID>` — id из вывода `yc vpc security-group create` (или `yc vpc security-group list`).
После создания команда выведет внешний IP (`one_to_one_nat.address`) — понадобится дальше.

## 3. Деплой приложения

Подключаемся по SSH (имя пользователя обычно совпадает с локальным, если не указывали `--user`):

```bash
ssh <user>@<EXTERNAL_IP>
```

На сервере:

```bash
git clone https://github.com/alisamagarova/shortener.git
cd shortener
cp .env.example .env
```

В `.env` обязательно:
- сменить `POSTGRES_PASSWORD` на свой
- выставить `FRONTEND_PORT=80`

```bash
sudo docker compose up -d --build
```

## 4. Проверка

```bash
curl http://<EXTERNAL_IP>/                      # отдаёт index.html
curl http://<EXTERNAL_IP>/api/v1/health          # {"status":"ok"}
curl -X POST http://<EXTERNAL_IP>/api/v1/links \
  -H "Content-Type: application/json" \
  -d '{"originalUrl": "https://example.com"}'
```

Открыть `http://<EXTERNAL_IP>/` в браузере — должна открыться страница с полем
"Вставьте ссылку, которую нужно укоротить".

## 5. Обновление деплоя

```bash
cd shortener
git pull
sudo docker compose up -d --build
```

## Дальнейшие шаги (по желанию)

- Привязать домен (A-запись на `<EXTERNAL_IP>`) и настроить TLS — например, добавить
  контейнер `certbot` или поставить `nginx` + `certbot` прямо на хосте перед приложением.
- Настроить регулярный бэкап `db_data` (volume с данными PostgreSQL) — например,
  снапшотами диска Yandex Cloud или `pg_dump` по cron.
- Если нагрузка вырастет за пределы одной ВМ — вернуться к варианту с Managed PostgreSQL
  и несколькими инстансами backend за Application Load Balancer (тогда LRU-кэш и
  rate limiter нужно будет вынести в Redis, см. README).
