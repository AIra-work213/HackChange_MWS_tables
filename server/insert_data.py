import requests
import pandas as pd
import math
import time
from pathlib import Path

# Конфигурация API
URL = "https://tables.mws.ru/fusion/v1/datasheets/dst1M1JJWmGM2dChGF/records"
PARAMS = {
    "viewId": "viwYvxvon7TBU",
    "fieldKey": "name"
}
HEADERS = {
    "Authorization": "Bearer uskSID2MFKEnL7AVNUdLrnn",
    "Content-Type": "application/json"
}

# Лимит записей за один запрос
BATCH_SIZE = 1000

# Маппинг колонок CSV -> колонки API
COLUMN_MAPPING = {
    "id_post": "post_id",           # id_post -> post_id
    "title": "title",               # title -> title
    "text": "text",                 # text -> text
    "views": "views",               # views -> views
    "likes": "likes",               # likes -> likes
    "reposts": "reposts",           # reposts -> reposts
    "comments": "comments",         # comments -> comments (текст комментариев)
    "date_time": "post_date_time",  # date_time -> post_date_time (timestamp)
    "id_group": "owner_id",         # id_group -> owner_id
    "ER": "ER",                     # ER -> ER
    "Efficiency": "Efficiency",     # Efficiency -> Efficiency
    "day_of_week": "day_of_week",   # day_of_week -> day_of_week
    "date": "post_date",            # date -> post_date
    "time_period": "time_period",   # time_period -> time_period
}


def load_csv(csv_path: str) -> pd.DataFrame:
    """Загружает CSV файл и возвращает DataFrame."""
    df = pd.read_csv(csv_path)
    print(f"Загружено {len(df)} записей из CSV")
    print(f"Колонки в CSV: {list(df.columns)}")
    return df


def transform_row(row: pd.Series) -> dict:
    """Преобразует строку DataFrame в формат API."""
    fields = {}
    
    for csv_col, api_col in COLUMN_MAPPING.items():
        if csv_col in row.index:
            value = row[csv_col]
            
            # Пропускаем NaN значения
            if pd.isna(value):
                continue
            
            # Преобразование типов
            if api_col in ["views", "likes", "reposts", "comments_count"]:
                # Целочисленные поля
                fields[api_col] = int(value)
            elif api_col in ["ER"]:
                # Числа с плавающей точкой
                fields[api_col] = float(value)
            elif api_col in ["post_date_time"]:
                # Timestamp (в секундах), преобразуем в миллисекунды
                ts = int(value)
                if ts < 10**12:
                    ts = ts * 1000
                fields[api_col] = ts
            elif api_col in ["post_date"]:
                # Дата в формате YYYY-MM-DD, преобразуем в timestamp миллисекунды
                try:
                    from datetime import datetime
                    dt = datetime.strptime(str(value), "%Y-%m-%d")
                    fields[api_col] = int(dt.timestamp() * 1000)
                except ValueError:
                    # Если не удалось распарсить, пропускаем
                    pass
            elif api_col in ["post_id", "owner_id"]:
                # Строковые ID
                fields[api_col] = str(int(value)) if isinstance(value, float) else str(value)
            else:
                # Строковые поля
                fields[api_col] = str(value)
    
    # Вычисляемые поля
    if "text" in fields and fields["text"]:
        fields["len_text"] = len(fields["text"])
    
    return fields


def upload_batch(records: list) -> tuple[bool, str]:
    """Загружает пакет записей в API."""
    data = {
        "records": [{"fields": r} for r in records],
        "fieldKey": "name"
    }
    
    try:
        response = requests.post(URL, params=PARAMS, headers=HEADERS, json=data, timeout=60)
        
        if response.status_code in [200, 201]:
            return True, f"OK: загружено {len(records)} записей"
        else:
            return False, f"Ошибка {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, f"Исключение: {str(e)}"


def upload_csv(csv_path: str, max_records: int = None, start_from: int = 0):
    """
    Загружает данные из CSV в API.
    
    Args:
        csv_path: Путь к CSV файлу
        max_records: Максимальное количество записей для загрузки (None = все)
        start_from: Начать с записи номер N (для продолжения загрузки)
    """
    # Загружаем CSV
    df = load_csv(csv_path)
    
    # Ограничиваем количество записей
    if start_from > 0:
        df = df.iloc[start_from:]
    if max_records:
        df = df.head(max_records)
    
    total_records = len(df)
    total_batches = math.ceil(total_records / BATCH_SIZE)
    
    print(f"\nНачинаем загрузку {total_records} записей ({total_batches} пакетов по {BATCH_SIZE})")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, total_records)
        
        batch_df = df.iloc[start_idx:end_idx]
        records = [transform_row(row) for _, row in batch_df.iterrows()]
        
        # Фильтруем пустые записи
        records = [r for r in records if r]
        
        if not records:
            print(f"Пакет {batch_num + 1}/{total_batches}: пропущен (нет данных)")
            continue
        
        success, message = upload_batch(records)
        
        if success:
            success_count += len(records)
            print(f"Пакет {batch_num + 1}/{total_batches}: {message}")
        else:
            error_count += len(records)
            print(f"Пакет {batch_num + 1}/{total_batches}: {message}")
        
        # Задержка между запросами чтобы не превысить rate limit
        if batch_num < total_batches - 1:
            time.sleep(0.5)
    
    print("-" * 50)
    print(f"Загрузка завершена!")
    print(f"Успешно: {success_count} записей")
    print(f"Ошибок: {error_count} записей")


if __name__ == "__main__":
    csv_file = Path(__file__).parent.parent / "telecom_operators_posts-2.csv"
    
    if not csv_file.exists():
        print(f"Файл не найден: {csv_file}")
        exit(1)
        
    upload_csv(str(csv_file), max_records=None)





