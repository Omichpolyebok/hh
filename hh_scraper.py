# requirements: requests, pandas, openpyxl, pymorphy2 (опционально)
# pip install requests pandas openpyxl pymorphy2

import requests
import pandas as pd
import re
import time
from collections import Counter

# === Настройки поиска ===
BASE_URL = "https://api.hh.ru/vacancies"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; HH-Analyzer/1.0)"}

QUERY = "программист"
AREAS = [72]  # Пермь
PAGES = 7       # сколько страниц просканировать
PER_PAGE = 50   # вакансий на странице
PAUSE = 0.5     # пауза между запросами (секунд)
# === Словарь технологий ===
KW_MAP = {
    # --- 1С / ERP ---
    "1с": "1С", "1c": "1С", "erp": "ERP", "автоматизация": "Automation",
    # --- Backend ---
    "python": "Python", "php": "PHP", "c#": "C#", "csharp": "C#", 
    "c++": "C++", "cpp": "C++", "java": "Java", "scala": "Scala", "pascal": "Pascal",
    # --- Frameworks ---
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI", "sqlalchemy": "SQLAlchemy",
    "alembic": "Alembic", "laravel": "Laravel", "symfony": "Symfony", "yii": "Yii",
    "qt": "Qt", "qml": "Qt/QML", "wpf": "WPF", "rest": "REST API", "rest api": "REST API",
    "graphql": "GraphQL", "solid": "SOLID", "ооп": "OOP", "объектно-ориентированное": "OOP",
    "структурное программирование": "Structured Programming", "многопоточность": "Multithreading",
    # --- Databases ---
    "postgres": "PostgreSQL", "postgresql": "PostgreSQL", "mysql": "MySQL",
    "clickhouse": "ClickHouse", "tarantool": "Tarantool", "redis": "Redis",
    "oracle": "Oracle", "mssql": "MS SQL Server", "sql server": "MS SQL Server",
    "sqlite": "SQLite", "sql": "SQL", "pl/sql": "PL/SQL",
    # --- Web / Frontend ---
    "html": "HTML", "css": "CSS", "js": "JavaScript", "javascript": "JavaScript",
    # --- DevOps ---
    "git": "Git", "tfs": "TFS", "ci/cd": "CI/CD", "docker": "Docker",
    "kubernetes": "Kubernetes", "k8s": "Kubernetes", "grafana": "Grafana", "zabbix": "Zabbix",
    "vpn": "VPN", "ssl": "SSL/TLS", "tls": "SSL/TLS", "linux": "Linux",
    # --- Soft skills ---
    "английский": "English", "english": "English",
    "работа в команде": "Teamwork", "ответственность": "Responsibility",
    "обучаемость": "Learning Ability", "коммуникабельность": "Communication",
}

# === Вспомогательные функции ===

def normalize(text: str) -> str:
    text = text.lower()
    return re.sub(r"[^а-яa-z0-9\.\+#\-\s]", " ", text)

def count_keywords(text: str) -> Counter:
    t = normalize(text)
    counts = Counter()
    for token, canon in KW_MAP.items():
        if re.search(r'\b' + re.escape(token) + r'\b', t):
            counts[canon] += 1
    return counts

def fetch_vacancies(area, page):
    params = {"text": QUERY, "area": area, "page": page, "per_page": PER_PAGE, "experience": "noExperience",}
    r = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()

def fetch_description(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return ""
    data = r.json()
    desc = data.get("description", "") or ""
    skills = " ".join([s["name"] for s in data.get("key_skills", [])])
    return desc + " " + skills

# === Основной процесс ===
# === Основной процесс ===
def main():
    all_counts = Counter()
    all_rows = []

    for area in AREAS:
        for page in range(PAGES):
            print(f"[area={area}] fetch page {page}")
            data = fetch_vacancies(area, page)

            for item in data.get("items", []):
                vac_id = item["id"]
                api_url = f"https://api.hh.ru/vacancies/{vac_id}"

                try:
                    text = fetch_description(api_url)
                    counts = count_keywords(text)

                    # 🟢 Берём только уникальные технологии из этой вакансии
                    unique_stacks = set(counts.keys())
                    for stack in unique_stacks:
                        all_counts[stack] += 1

                    all_rows.append({
                        "vacancy": item["name"],
                        "city": item["area"]["name"],
                        "url": item["alternate_url"],
                        "stacks": ", ".join(unique_stacks)
                    })

                    time.sleep(PAUSE)

                except Exception as e:
                    print("fail:", vac_id, e)

    # === Сохранение статистики ===
    df_summary = (
        pd.DataFrame(all_counts.items(), columns=["stack", "vacancies_count"])
        .sort_values("vacancies_count", ascending=False)
    )
    df_summary.to_excel("hh_stacks_summary3.xlsx", index=False)

    df_detailed = pd.DataFrame(all_rows)
    df_detailed.to_excel("hh_vacancies_detailed3.xlsx", index=False)

    print("\nTOP 20 технологий (по количеству вакансий):")
    print(df_summary.head(20))


if __name__ == "__main__":
    main()
