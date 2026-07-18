---

<p align="center">
  <a href="https://pay.cloudtips.ru/p/5675a192" target="_blank" rel="noopener">
    <img alt="Поддержать проект"
         src="https://img.shields.io/badge/💛%20Поддержать%20проект-00D1B2?style=for-the-badge&labelColor=222">
  </a>
  <a href="https://pay.cloudtips.ru/p/5675a192" target="_blank" rel="noopener">
    <img alt="CloudTips"
         src="https://img.shields.io/badge/CloudTips-0088CC?style=for-the-badge&labelColor=111">
  </a>
</p>

---

# ONVIF/RTSP Camera Audit Script

Скрипт для автоматического аудита IP-камер с поддержкой ONVIF и RTSP.
Для интеграции с системами мониторинга **Zabbix** через внешние обработки.

---

## Возможности

- 🔍 Поиск доступных ONVIF-портов и рабочих учетных данных (перебор известных паролей).
- 📜 Получение информации о камере:
  - Производитель (Manufacturer)
  - Модель (Model)
  - Версия прошивки (FirmwareVersion)
  - Серийный номер (SerialNumber)
  - Аппаратный ID (HardwareId)
- 🌐 Сбор сетевых настроек:
  - MAC-адрес
  - IP-адрес
  - Настройки NTP и DNS
- ⏱ Проверка синхронизации времени с камерой (допустимое расхождение времени настраивается).
- 👥 Аудит пользователей камеры:
  - Сохранение базовой линии пользователей.
  - Обнаружение новых или измененных учетных записей.
- 🎥 Проверка RTSP-потока:
  - Захват кадров с анализом (размер кадра, яркость, изменения между кадрами, FPS).
  - Фолбэк проверка потока через `ffprobe`, если OpenCV не справился.
  - Диагностика цветового баланса с определением «фиолетового», «жёлтого» и «зелёного» сдвига матрицы.
- 🔐 Диагностика ONVIF-методов: фиксируются анонимно открытые, защищённые и неподдерживаемые вызовы.

---
## Преимущества

- ⚡ **Быстрая интеграция**  
  Нет необходимости вручную подбирать ONVIF-порты, ссылки RTSP или параметры для разных производителей камер.

- 🔗 **Автоматическое определение параметров**  
  Скрипт сам находит рабочий ONVIF-порт и RTSP-поток без необходимости прописывать макросы или вручную настраивать узлы в Zabbix.

- 🛠️ **Минимальная настройка в Zabbix**  
  Для мониторинга камеры достаточно только IP-адреса. Нет необходимости заполнять макросы вроде `{$PORT}`, `{$USERNAME}`, `{$PASSWORD}`. (не забудьте изменить/добавить пароли в `param.py` — константы `DEFAULT_USERNAME`, `DEFAULT_PASSWORD`, `PASSWORDS`)

- 🚀 **Универсальная совместимость**  
  Работает с большинством камер, поддерживающих стандарт ONVIF, независимо от производителя или модели.

- 🔒 **Безопасность и аудит**  
  Позволяет отслеживать появление новых пользователей и проверять корректность настройки времени на камере.

---
## Подготовка окружения и установка

Инструкция рассчитана на "чистый" сервер Zabbix (Ubuntu/Debian) и пользователя,
который ранее не работал с Python-скриптами.

### 1. Проверяем наличие Python

```bash
python3 --version
```

* Если версия ниже 3.11, установите обновленный Python (например, из пакета
  `python3.11` или с официального сайта).

### 2. Создаем рабочий каталог

Все файлы проекта должны лежать вместе, чтобы импорты модулей работали
корректно. В каталоге `externalscripts` Zabbix должны находиться **все** `.py`
файлы из репозитория: `camcheck.py`, `baseline.py`, `param.py`,
`onvif_utils.py`, `rtsp_utils.py`, `cli.py` и другие вспомогательные модули.

```bash
sudo mkdir -p /usr/lib/zabbix/externalscripts/onvif_audit
sudo chown -R zabbix:zabbix /usr/lib/zabbix/externalscripts
```

### 3. Скачиваем проект

```bash
cd /tmp
wget https://github.com/RoganovDA/Onvif_RTSP_ZABBIX/archive/refs/heads/main.zip -O Onvif_RTSP_ZABBIX.zip
unzip Onvif_RTSP_ZABBIX.zip
cd Onvif_RTSP_ZABBIX-main
```

При обновлении скрипта удалите старые версии файлов проекта, чтобы не
оставались устаревшие модули (осторожно: команда удаляет только файлы
камчека, а не все внешние скрипты):

```bash
sudo rm -f /usr/lib/zabbix/externalscripts/{camcheck.py,baseline.py,param.py,onvif_utils.py,rtsp_utils.py,cli.py}
```

Затем копируем все `.py` файлы и файлы с настройками:

```bash
sudo cp *.py /usr/lib/zabbix/externalscripts/
sudo chown zabbix:zabbix /usr/lib/zabbix/externalscripts/*.py
sudo chmod 750 /usr/lib/zabbix/externalscripts/*.py
```

> **Важно:** не копируйте выборочно файлы — без вспомогательных модулей
> `onvif_utils.py` или `rtsp_utils.py` скрипт упадет с ошибкой импорта.

### 4. Настраиваем виртуальное окружение (опционально, но рекомендовано)

```bash
python3 -m venv /usr/lib/zabbix/externalscripts/venv
source /usr/lib/zabbix/externalscripts/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

Чтобы Zabbix использовал виртуальное окружение, добавьте в `/etc/zabbix/zabbix_server.conf`:

```
ExternalScripts=/usr/lib/zabbix/externalscripts
```

И перезапустите службу:

```bash
sudo systemctl restart zabbix-server
```

Если виртуальное окружение не используется, установите зависимости глобально:

```bash
sudo -H python3 -m pip install --upgrade pip
sudo -H python3 -m pip install -r requirements.txt
```

### 5. Устанавливаем системные утилиты

`ffmpeg`/`ffprobe` нужны для резервной проверки RTSP потока.

```bash
sudo apt update
sudo apt install ffmpeg
```

### 6. Проверяем права доступа

Пользователь `zabbix` должен иметь права на чтение/запуск `.py` файлов и запись
в каталог `onvif_audit` (для хранения результатов аудита).

```bash
sudo chown -R zabbix:zabbix /usr/lib/zabbix/externalscripts
sudo chmod 750 /usr/lib/zabbix/externalscripts/*.py
sudo chmod 770 /usr/lib/zabbix/externalscripts/onvif_audit
```

### 7. Первичная настройка параметров

Отредактируйте файл `param.py`, чтобы указать собственные списки логинов и
паролей, таймауты и другие параметры перебора.

```bash
sudo nano /usr/lib/zabbix/externalscripts/param.py
```

После сохранения изменений перезапуск Zabbix не требуется.

### 8. Проверяем запуск вручную

Перед подключением к Zabbix протестируйте скрипт в консоли:

```bash
sudo -u zabbix python3 /usr/lib/zabbix/externalscripts/camcheck.py 192.0.2.10 --debug
```

Замените `192.0.2.10` на IP-адрес тестовой камеры. Если выводится JSON с
информацией, значит установка выполнена корректно. При ошибках проверьте, что:

1. Все `.py` файлы лежат в каталоге `externalscripts`.
2. Установлены все зависимости из `requirements.txt`.
3. Пользователь `zabbix` имеет доступ в интернет/к камере.

---

## Использование

```bash
./camcheck.py <IP-адрес камеры> [--logfile /path/to/log] [--debug] [--username USERNAME] [--password PASSWORD] [--ping-timeout SECONDS]
```

Опции:
- `--logfile` — путь для записи логов (только для отладки);
- `--debug` — включить подробное логирование;
- `--username` — имя пользователя для камеры;
- `--password` — пароль пользователя;
- `--ping-timeout` — таймаут проверки доступности, сек.
- `--full-output` — вернуть полный расширенный JSON (как в предыдущих версиях).



По умолчанию скрипт возвращает плоский JSON-отчёт, совместимый с предыдущими версиями:

```json
{
    "Manufacturer": "ActiveCam",
    "Model": "AC-D8111IR2",
    "FirmwareVersion": "IPCAM_V2.46.170906",
    "SerialNumber": "D8111IR2M07Z031870873",
    "HardwareId": "600110002-BV-H1002",
    "HwAddress": "f0:23:b9:45:33:69",
    "Address": "10.0.6.101",
    "DNSname": null,
    "TimeSyncOK": true,
    "TimeDifferenceSeconds": 0,
    "ONVIFStatus": "success",
    "NewUsersDetected": false,
    "NewUsernames": [],
    "RemovedUsernames": [],
    "BaselineCreated": false,
    "UserCount": 1,
    "RTSPPort": 101,
    "RTSPPath": "/live/main",
    "RTSPTransport": "tcp",
    "RTSPBestURI": "rtsp://user:***@10.0.6.101/live/main",
    "status": "ok",
    "frames_read": 53,
    "avg_frame_size_kb": 3600.0,
    "width": 1280,
    "height": 960,
    "avg_brightness": 131.98,
    "frame_change_level": 0.1,
    "real_fps": 17.67,
    "note": "",
    "ColorDiagnosis": "balanced",
    "ColorConfidence": 0.94,
    "ColorStability": "stable",
    "ColorDominantChannel": "green",
    "ColorTriggeredMetrics": null,
    "ColorMaxVariance": 6.1,
    "ColorMaxRatio": 1.08,
    "ColorFrameCount": 53,
    "ColorReason": "No significant colour cast detected",
    "ColorRatios": {
        "blue_green": 0.92,
        "red_green": 1.04,
        "red_blue": 1.13,
        "green_blue": 1.09,
        "green_red": 0.96,
        "max_min": 1.13
    },
    "ColorBalance": {
        "blue": 0.33,
        "green": 0.34,
        "red": 0.33
    },
    "ColorChannels": {
        "blue": 108.2,
        "green": 111.4,
        "red": 119.0
    },
    "Notes": [],
    "NextAttemptAfter": null
}
```

Чтобы получить расширенный отчёт с подробными фазами (`phase.*`), потоковыми попытками и списком предупреждений, используйте флаг `--full-output`.

**Пояснения к полям безопасности:**

- `ONVIFStatus` — итог статуса подключения (`success`, `unauthorized`, `locked`, `not_supported`).
- Детализация по проверенным методам (какие доступны анонимно, требуют логина или не поддерживаются) сохраняется в файле аудита `onvif_audit/<IP>_users.json`.

**Поля анализа изображения:**

- `ColorDiagnosis` — итоговый диагноз цветового баланса (`balanced`, `purple`, `yellow`, `green`, `unknown`).
- `ColorConfidence` — уверенность детектора (0–1); чем ближе к 1, тем надёжнее вывод.
- `ColorStability` и `ColorMaxVariance` — оценка стабильности сцены между кадрами (помогает отличать вспышки от постоянного сдвига).
- `ColorRatios`, `ColorBalance`, `ColorChannels` — подробные числовые метрики по каналам B/G/R.
- `ColorTriggeredMetrics` — какие соотношения каналов превысили порог при обнаружении перекоса.

---

## Базовая линия пользователей

Скрипт сохраняет найденных пользователей, пароль и параметры подключения в каталог
`onvif_audit`. Для каждой камеры создаются файлы `<IP>_users.json` и
`<IP>_progress.json`, позволяющие отслеживать изменения учётных записей и не
повторять уже проверенные пароли. В `<IP>_users.json` дополнительно фиксируются
списки открытых, защищённых и неподдерживаемых методов (`open_methods`,
`protected_methods`, `unsupported_methods`), а также подробная матрица результатов
(`method_status`) для последующего аудита.

---

## Интеграция с Zabbix

- Тип элемента данных: `External Check`
- Ключ вызова:  
  ```bash
  camcheck.py["{HOST.IP}"]
  ```
- Тип данных: **Текст**
- Предобработка на элементе:
  - **JSONPath** для извлечения нужных полей (например, `$.status`, `$.TimeSyncOK`).

На основе полей можно строить триггеры:
- "Камера недоступна по ONVIF"
- "Ошибка подключения RTSP-потока"
- "Обнаружен новый пользователь на камере"
- "Сильное расхождение времени"
- "Смещение цветового баланса (фиолетовый/жёлтый/зелёный)"

### Импорт шаблона в Zabbix

1. Импортируйте файл `zbx_export_templates.yaml` через **Configuration → Templates → Import**.
2. После импорта назначьте шаблон хост-группе `Security Cameras - AllCamers` или собственной группе камер.
3. Убедитесь, что на сервере присутствует внешний скрипт `camcheck.py` и он доступен пользователю `zabbix`.
4. Перед массовым применением запустите проверку синтаксиса YAML командой:

   ```bash
   zabbix_export validate zbx_export_templates.yaml
   ```

   > Если утилита `zabbix_export` отсутствует в окружении, установите пакет с CLI-утилитами Zabbix или выполните проверку на тестовом сервере.

### Макросы шаблона

| Макрос | Назначение | Значение по умолчанию |
|:-------|:-----------|:----------------------|
| `{$CAM_ENV}` | Значение тега `env` (профиль окружения) | `prod` |
| `{$CAMERA_IP}` | Передача IP-адреса в мастер-элемент | `{HOST.CONN}` |
| `{$CAM_NTP_EXPECTED}` | Ожидаемое имя NTP/DNS-сервера | `ntp.syshleb.ru` |
| `{$CAM_TIMEOUT}` | Временное окно для подтверждения событий | `30m` |
| `{$CAM_STATUS_WINDOW}` | Окно корреляции статусов RTSP | `30m` |
| `{$CAM_STATUS_ERROR_COUNT}` | Количество циклов с ошибками потока до тревоги | `3` |
| `{$CAM_STATUS_AUTH_THRESHOLD}` | Количество попыток `unauthorized` до эскалации | `3` |
| `{$CAM_STATUS_RECOVERY}` | Количество успешных опросов для снятия тревог | `3` |
| `{$CAM_STATUS_RECOVERY_WINDOW}` | Временное окно для восстановления | `30m` |
| `{$CAM_RTT_WARN}` | Допустимое среднее время выполнения `camcheck.py`, сек | `15` |
| `{$CAM_RTT_RECOVERY}` | Порог восстановления по времени выполнения, сек | `10` |
| `{$CAM_TIME_DRIFT_WARN}` | Максимальное допустимое смещение времени, сек | `5` |
| `{$CAM_TIME_DRIFT_RECOVERY}` | Целевое смещение времени после восстановления, сек | `2` |

### Теги и маршрутизация событий

- **Теги шаблона:** `service=camera`, `role=surveillance`, `env={$CAM_ENV}`.
- **Теги триггеров:**
  - `scope` (`security`/`performance`) — для маршрутизации медиа-типов.
  - `impact` (`auth`, `rtsp`, `time`, `nvps`, `integrity` и др.) — тип последствий.
  - `cause` (`credentials`, `stream`, `ntp`, `configuration`, `latency`, `hardware`).
  - `subsystem` (`rtsp`, `rtsp-auth`, `time-sync`, `externalscripts`, `inventory`, `accounts`).
  - `severity` — дублирует важность, облегчая фильтрацию в отчётах.
- Для уведомлений настройте маршруты на основе `scope=security` (безопасность) и `scope=performance` (эксплуатация).

### Импорт шаблона

1. В меню **Configuration → Templates → Import** укажите файл `zbx_export_templates.yaml`.
2. В окне импорта оставьте действие «Create new», чтобы новые сущности добавились, не перезаписывая существующие.
3. После импорта убедитесь, что в шаблоне корректно подключены элементы и триггеры, и при необходимости адаптируйте макросы.

### Оповещения и эскалации

| Событие (триггер) | Сообщение | Канал | SLA/Реакция |
|:------------------|:----------|:------|:------------|
| `scope=security`, `impact=auth` (несанкционированный доступ, новые пользователи) | «🚨 Камера {HOST.NAME}: {EVENT.NAME}. Последний статус: {ITEM.VALUE}. Ссылка на график: {TRIGGER.URL}» | Telegram/SMS дежурного офицера | Реакция ≤ 15 мин |
| `scope=performance`, `impact=rtsp` (ошибки потока) | «📡 Камера {HOST.NAME}: {EVENT.NAME}. fps={ITEM.LASTVALUE1}, exec={ITEM.LASTVALUE2}s» | Ops чат (Mattermost/Slack) | Реакция ≤ 30 мин |
| `scope=performance`, `impact=time` (NTP, смещение времени) | «⏰ Камера {HOST.NAME}: {EVENT.NAME}. Разница времени {ITEM.VALUE}s» | Email ИБ/админов | Плановое исправление ≤ 4 ч |
| `scope=performance`, `impact=nvps` (долгие выполнения) | «⚙️ Camcheck длится {ITEM.VALUE}s (порог {$CAM_RTT_WARN}) — проверите нагрузку внешних обработок» | Ops чат | Анализ при превышении 2 циклов |
| `scope=security`, `impact=integrity` (замена камеры) | «🛠️ {EVENT.NAME}. Предыдущая модель: {ITEM.PREVVALUE1}, новая: {ITEM.VALUE1}» | Email CISO + ServiceDesk | Создание инцидента |

Рекомендуемый шаблон сообщения:

```
[{EVENT.TIME}] {EVENT.SEVERITY} {EVENT.SCOPE}: {EVENT.NAME}
Хост: {HOST.NAME}
Последнее значение: {ITEM.LASTVALUE}
Тэги: {EVENT.TAGS}
Графики: {TRIGGER.URL}
```

### Чек-лист внедрения

1. Установить зависимости и разместить скрипты в `externalscripts`.
2. Импортировать шаблон `zbx_export_templates.yaml`.
3. Настроить макросы `{$CAM_ENV}` и пороговые значения под окружение.
4. Привязать медиа-типы к тегам событий (`scope`, `impact`).
5. Добавить камеры в нужные группы и связать с шаблоном.
6. Провести тестовое оповещение (вручную переключить статус RTSP/NTP).
7. При необходимости создать собственные дашборды в Zabbix и зафиксировать их для отчётности.

---

## Параметры

| Параметр | Описание | Значение по умолчанию |
|:--------|:---------|:---------------------|
| `DEFAULT_USERNAME` | Имя пользователя по умолчанию | `admin` |
| `DEFAULT_PASSWORD` | Пароль по умолчанию для начальных попыток | `000000` |
| `PASSWORDS` | Список известных паролей для подбора | `["admin", "12345678", "000000"]` |
| `ALLOWED_TIME_DIFF_SECONDS` | Допустимое расхождение времени UTC, сек | `120` |
| `PORTS_TO_CHECK` | Список портов для проверки ONVIF | `[80, 8000, 8080, 8899, 10554, 10080, 554, 37777, 5000, 443]` |
| `MAX_PASSWORD_ATTEMPTS` | Максимальное число попыток подбора пароля | `5` |
| `MAX_MAIN_ATTEMPTS` | Максимальное число основных попыток соединения | `3` |
| `RTSP_PATH_CANDIDATES` | Список типовых RTSP-путей при отсутствии данных от ONVIF | `["/Streaming/Channels/101", "/h264", "/live", "/stream1"]` |
| `DEFAULT_RTSP_PORT` | RTSP-порт по умолчанию | `554` |
| `CV2_OPEN_TIMEOUT_MS` | Таймаут открытия RTSP в OpenCV, мс | `5000` |
| `CV2_READ_TIMEOUT_MS` | Таймаут чтения кадра в OpenCV, мс | `5000` |
| `COLOR_CAST_RULES` | Пороги для определения цветового перекоса | см. `param.py` |
| `COLOR_CONFIDENCE_SCALE` | Масштаб для расчёта уверенности диагноза | `0.35` |
| `COLOR_VARIANCE_STABLE_THRESHOLD` | Граница стабильности сцены | `25.0` |
| `ONVIF_PRIORITY_METHODS` | Приоритетный список методов для проверки авторизации (сервис, метод, параметры) | см. `param.py` |

---

## Требования

**Все зависимости обязательны!**

- Python 3.11+
- Установленные библиотеки Python (см. `requirements.txt`):
  - `onvif` (пакет `onvif-zeep`)
  - `opencv-python`
  - `numpy`
  - `zeep`
- Установленные системные утилиты `ffmpeg` и `ffprobe`
---

## TODO

- ✅ Базовая поддержка ONVIF и RTSP камер.
- ✅ Проверка времени и аудит пользователей.
- ✅ Интеграция в Zabbix через внешние обработки.
- ✅ Шаблон для Zabbix 7.0, 7.2
- ✅ Расширенная диагностика RTSP потока: битрейт, кодек, аудио-потоки.
- ✅ Улучшение обработки ошибок и логирование в отдельный файл.

## Performance tuning

### External checks

`camcheck.py` is executed as a Zabbix **External check**. External checks are processed by the standard Zabbix pollers (`StartPollers`).

For installations with a large number of cameras, the default poller count may cause too many simultaneous RTSP/ONVIF connections and increase CPU load.

Recommended settings for Raspberry Pi and other low-power systems:

```ini
# /etc/zabbix/zabbix_server.conf

StartPollers=3
Timeout=30
```

After changing the configuration, restart the server:

```bash
sudo systemctl restart zabbix-server
```

Verify that the new poller count is active:

```bash
ps -ef | grep '[z]abbix_server: poller'
```

Example output:

```
zabbix_server: poller #1
zabbix_server: poller #2
zabbix_server: poller #3
```

### Recommended update interval

For installations with more than **100 cameras**, it is recommended to increase the master item update interval:

```yaml
delay: 30m
```

This significantly reduces CPU and network load while still providing reliable camera health monitoring.

---

## Лицензия

MIT License — свободное использование и модификация с сохранением авторства.

---

## Авторы

- [RoganovDA](https://github.com/RoganovDA)

---


