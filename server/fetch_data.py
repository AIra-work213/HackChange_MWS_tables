import requests
import json
from langchain_core.tools import tool

# Конфигурация
# Вставьте ваш токен здесь
API_TOKEN = "uskSID2MFKEnL7AVNUdLrnn" 
BASE_URL = "https://tables.mws.ru/fusion/v1/datasheets/dstCNkL7G9iYsD0LY9/records"
DEFAULT_VIEW_ID = "viwYvxvon7TBU"

@tool
def get_records_from_model_query(query_params):
    """
    Выполняет GET запрос к API, используя параметры из словаря (ответа модели).
    """

    params = {
        "viewId": DEFAULT_VIEW_ID,
        "fieldKey": "name"
    }

    for key, value in query_params.items():
        if key == 'sort' and isinstance(value, list):
            # Специальный формат для sort: sort[0][field]=likes&sort[0][order]=desc
            for i, sort_item in enumerate(value):
                if isinstance(sort_item, dict):
                    for sort_key, sort_value in sort_item.items():
                        params[f"sort[{i}][{sort_key}]"] = sort_value
        elif key == 'fields' and isinstance(value, list):
            # fields через запятую
            params[key] = ",".join(value)
        elif isinstance(value, (list, dict)):
            # Остальные массивы/объекты как JSON
            params[key] = json.dumps(value, separators=(',', ':'))
        else:
            params[key] = value

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"Отправка запроса с параметрами: {params}")
    try:
        response = requests.get(BASE_URL, params=params, headers=headers)
        print(f"URL запроса: {response.url}") # Для отладки
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        if 'response' in locals():
            print(f"Тело ответа: {response.text}")
        return None


if __name__ == "__main__":
    # Эмуляция ответа от модели (как в test.py)
    # Пример: "Топ-5 постов по лайкам"
    fake_model_output = {
        "pageSize": 5,
        "sort": [{"field": "ER", "order": "asc"}],
        "fields": ["title", "text", "ER", "Efficiency"]
    }
    
    print(f"--- Входные данные от модели ---\n{fake_model_output}\n")
    
    data = get_records_from_model_query.invoke({"query_params": fake_model_output})
    
    if data:
        print("\n--- Ответ API ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))