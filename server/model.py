from openai import OpenAI
import json
import time
from fetch_data import get_records_from_model_query


class MyModel:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key="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",
        )
        
        # Модель для использования
        self.model_name = "tngtech/deepseek-r1t2-chimera:free"
        # Хранилище сессий для памяти контекста
        self.sessions: dict[str, list[dict]] = {}
        
        self.max_history = 10
        
        # Максимальное количество запросов к БД за один вопрос пользователя
        self.max_db_queries = 5
        
        # Системный промпт для агента с множественными запросами
        self.agent_system_prompt = """Ты продвинутый ИИ-агент для анализа данных постов. Ты можешь выполнять НЕСКОЛЬКО запросов к базе данных для сложного анализа.

База данных содержит следующие поля:
- post_id: Идентификатор поста
- title: Заголовок поста (может быть NaN)
- text: Текст поста (может быть NaN)
- attachment_description: Описание вложения
- views: Количество просмотров
- likes: Количество лайков
- reposts: Количество репостов
- comments_count: Количество комментариев
- comments: Текст комментариев
- post_date: Дата публикации поста (в миллисекундах с 1970 года)
- owner_id: Идентификатор владельца поста
- ER: Engagement Rate
- Efficiency: Эффективность поста (Очень низкая, Низкая, Средняя, Высокая, Очень высокая)
- day_of_week: День недели
- time_period: Время суток (Утро, День, Вечер, Ночь)
- len_text: Длина текста поста

ФОРМАТ ОТВЕТА - СТРОГО JSON:

1. Если нужно сделать запрос к БД:
{
    "action": "query",
    "reason": "Краткое пояснение зачем этот запрос",
    "query": {
        "pageSize": 100,
        "sort": [{"field": "likes", "order": "desc"}],
        "fields": ["title", "text", "likes"],
        "filterByFormula": "{views} > 100",
        "maxRecords": 1000
    }
}

2. Если данных достаточно для ответа:
{
    "action": "answer",
    "response": "Полный ответ пользователю на русском языке с анализом данных"
}

ПРИМЕРЫ СЛОЖНОГО АНАЛИЗА:

Запрос: "Сравни эффективность постов утром и вечером"
Шаг 1: {"action": "query", "reason": "Получаю посты за утро", "query": {"filterByFormula": "{time_period} = 'Утро'", "fields": ["ER", "likes", "views", "Efficiency"]}}
Шаг 2: {"action": "query", "reason": "Получаю посты за вечер", "query": {"filterByFormula": "{time_period} = 'Вечер'", "fields": ["ER", "likes", "views", "Efficiency"]}}
Шаг 3: {"action": "answer", "response": "Анализ показывает, что..."}

ПРАВИЛА:
1. Для сложных сравнений делай несколько запросов
2. Используй предыдущие результаты для формирования следующих запросов
3. Когда собрано достаточно данных — отвечай с action: "answer"
4. В ответе анализируй ВСЕ собранные данные
5. Отвечай ТОЛЬКО валидным JSON, без дополнительного текста"""

    def get_session(self, session_id: str) -> list[dict]:
        """Получает или создаёт сессию."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]
    
    def add_to_history(self, session_id: str, role: str, content: str):
        """Добавляет сообщение в историю сессии."""
        history = self.get_session(session_id)
        history.append({"role": role, "content": content})
        
        if len(history) > self.max_history * 2:
            self.sessions[session_id] = history[-(self.max_history * 2):]
    
    def clear_session(self, session_id: str):
        """Очищает историю сессии."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def _parse_json(self, response: str) -> dict:
        """Парсит JSON из ответа модели."""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start == -1 or end == 0:
                return {"error": "No JSON found in response"}
            json_text = response[start:end]
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse JSON: {str(e)}"}
    
    def _execute_db_query(self, query_params: dict) -> dict:
        """Выполняет запрос к базе данных."""
        try:
            records = get_records_from_model_query.invoke({"query_params": query_params})
            return records
        except Exception as e:
            return {"error": str(e)}
    
    def _call_llm(self, messages: list, max_retries: int = 3) -> str:
        """Вызывает LLM с обработкой rate limit."""
        for attempt in range(max_retries):
            try:
                completion = self.client.chat.completions.create(
                    extra_body={},
                    model=self.model_name,
                    messages=messages
                )
                return completion.choices[0].message.content
            except Exception as e:
                raise
        raise Exception("Превышен лимит попыток вызова LLM")

    def answer_query(self, query: str, session_id: str = "default") -> str:
        """Отвечает на запрос пользователя с возможностью множественных запросов к БД."""
        history = self.get_session(session_id)
        
        collected_data = []
        
        messages = [{"role": "system", "content": self.agent_system_prompt}]
        
        for msg in history[-6:]:
            messages.append(msg)
        
        messages.append({"role": "user", "content": f"Запрос пользователя: {query}"})
        
        for iteration in range(self.max_db_queries):
            print(f"\n--- Итерация {iteration + 1} ---")
            
            try:
                agent_response = self._call_llm(messages)
            except Exception as e:
                return f"Ошибка при обращении к AI: {str(e)}"
            
            print(f"Ответ агента: {agent_response[:500]}...")
            
            parsed = self._parse_json(agent_response)
            
            if "error" in parsed:
                print(f"Ошибка парсинга: {parsed['error']}")
                if collected_data:
                    messages.append({"role": "assistant", "content": agent_response})
                    messages.append({
                        "role": "user", 
                        "content": "Пожалуйста, сформулируй финальный ответ в формате JSON: {\"action\": \"answer\", \"response\": \"твой ответ\"}"
                    })
                    continue
                return agent_response
            
            action = parsed.get("action", "")
            
            if action == "answer":
                answer = parsed.get("response", "Не удалось сформировать ответ")
                print(f"Финальный ответ: {answer[:200]}...")
                
                self.add_to_history(session_id, "user", query)
                self.add_to_history(session_id, "assistant", answer)
                
                return answer
            
            elif action == "query":
                reason = parsed.get("reason", "")
                query_params = parsed.get("query", {})
                
                print(f"Запрос к БД ({reason}): {json.dumps(query_params, ensure_ascii=False)}")
                
                db_result = self._execute_db_query(query_params)
                
                collected_data.append({
                    "reason": reason,
                    "query": query_params,
                    "result": db_result
                })
                
                messages.append({"role": "assistant", "content": agent_response})
                
                result_summary = json.dumps(db_result, ensure_ascii=False, indent=2)
                if len(result_summary) > 3000:
                    result_summary = result_summary[:3000] + "\n... (данные обрезаны)"
                
                messages.append({
                    "role": "user",
                    "content": f"Результат запроса ({reason}):\n{result_summary}\n\nПродолжай анализ. Если нужны ещё данные - сделай ещё запрос. Если данных достаточно - дай финальный ответ."
                })
                
                record_count = len(db_result.get('records', [])) if isinstance(db_result, dict) else 'N/A'
                print(f"Получено записей: {record_count}")
            
            else:
                print(f"Неизвестное действие: {action}")
                messages.append({"role": "assistant", "content": agent_response})
                messages.append({
                    "role": "user",
                    "content": "Пожалуйста, ответь в правильном формате JSON с action: 'query' или 'answer'"
                })
        
        
        
        messages.append({
            "role": "user",
            "content": "Лимит запросов достигнут. Дай финальный ответ на основе собранных данных: {\"action\": \"answer\", \"response\": \"твой ответ\"}"
        })
        
        try:
            final_response = self._call_llm(messages)
        except Exception as e:
            return f"Ошибка при обращении к AI: {str(e)}"
        
        parsed = self._parse_json(final_response)
        
        answer = parsed.get("response", final_response) if "response" in parsed else final_response
        
        self.add_to_history(session_id, "user", query)
        self.add_to_history(session_id, "assistant", answer)
        
        return answer


if __name__ == "__main__":
    model = MyModel()
    query = "Сравни эффективность постов утром и вечером"
    response = model.answer_query(query)
    print("\n=== Response from model ===")
    print(response)
