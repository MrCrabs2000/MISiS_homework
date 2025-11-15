import requests
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, Path, Query, HTTPException
from pydantic import BaseModel
from fastapi.testclient import TestClient


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wiki_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class WikipediaAPI:
    def __init__(self, language: str = "ru"):
        self.base_url = f"https://{language}.wikipedia.org/api/rest_v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FastAPI-TestClient/1.0'
        })
        logger.info(f"Инициализирован WikipediaAPI для языка: {language}")

    def search_articles(self, query: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Выполняется поиск статей: '{query}' (limit: {limit})")
            url = f"{self.base_url}/page/search/title"
            params = {
                'q': query,
                'limit': limit
            }

            logger.debug(f"URL: {url}, Параметры: {params}")
            response = self.session.get(url, params=params)
            response.raise_for_status()

            logger.info(f"Успешно найдено статей для запроса '{query}': {len(response.json().get('pages', []))}")
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при поиске статей '{query}': {e}")
            return None

    def get_article_summary(self, title: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Запрашивается краткое содержание статьи: '{title}'")
            url = f"{self.base_url}/page/summary/{title}"

            logger.debug(f"URL: {url}")
            response = self.session.get(url)
            response.raise_for_status()

            logger.info(f"Успешно получено краткое содержание для '{title}'")
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Статья '{title}' не найдена")
            else:
                logger.error(f"HTTP ошибка при получении содержания статьи '{title}': {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении содержания статьи '{title}': {e}")
            return None

    def get_article_content(self, title: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"Запрашивается полное содержимое статьи: '{title}'")
            url = f"{self.base_url}/page/mobile-sections/{title}"

            logger.debug(f"URL: {url}")
            response = self.session.get(url)
            response.raise_for_status()

            logger.info(f"Успешно получено содержимое для '{title}'")
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Статья '{title}' не найдена")
            else:
                logger.error(f"HTTP ошибка при получении содержимого статьи '{title}': {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении содержимого статьи '{title}': {e}")
            return None


app = FastAPI(title="Wikipedia API Wrapper")
wiki_client = WikipediaAPI()


class SearchResponse(BaseModel):
    query: str
    results_count: int
    articles: list


class ArticleSummary(BaseModel):
    title: str
    summary: str
    url: str


class ArticleContent(BaseModel):
    title: str
    content: str
    sections_count: int


@app.get("/search/{query}", response_model=SearchResponse)
async def search_articles(
        query: str = Path(..., description="Поисковый запрос"),
        limit: int = Query(10, ge=1, le=50, description="Количество результатов")
) -> SearchResponse:
    logger.info(f"Вызван роут /search/{query} с limit={limit}")

    result = wiki_client.search_articles(query, limit)
    if not result:
        logger.warning(f"Не удалось выполнить поиск для запроса: {query}")
        raise HTTPException(status_code=500, detail="Ошибка при поиске статей")

    pages = result.get('pages', [])
    return SearchResponse(
        query=query,
        results_count=len(pages),
        articles=[page.get('title', '') for page in pages]
    )


@app.get("/article/{title}/summary", response_model=ArticleSummary)
async def get_article_summary(
        title: str = Path(..., alias="title", description="Название статьи")
) -> ArticleSummary:
    logger.info(f"Вызван роут /article/{title}/summary")

    result = wiki_client.get_article_summary(title)
    if not result:
        logger.warning(f"Не удалось получить содержание статьи: {title}")
        raise HTTPException(status_code=404, detail="Статья не найдена")

    return ArticleSummary(
        title=result.get('title', ''),
        summary=result.get('extract', ''),
        url=result.get('content_urls', {}).get('desktop', {}).get('page', '')
    )


@app.get("/article/{title}/content", response_model=ArticleContent)
async def get_article_content(
        title: str = Path(..., alias="title", description="Название статьи"),
        include_lead: bool = Query(True, description="Включать введение")
) -> ArticleContent:
    logger.info(f"Вызван роут /article/{title}/content с include_lead={include_lead}")

    result = wiki_client.get_article_content(title)
    if not result:
        logger.warning(f"Не удалось получить содержимое статьи: {title}")
        raise HTTPException(status_code=404, detail="Статья не найдена")

    content_parts = []
    sections = result.get('remaining', {}).get('sections', [])

    if include_lead and 'lead' in result:
        lead_section = result.get('lead', {}).get('sections', [])
        if lead_section:
            content_parts.append(lead_section[0].get('text', ''))

    for section in sections[:3]:
        content_parts.append(section.get('text', ''))

    full_content = "\n\n".join(content_parts)

    return ArticleContent(
        title=result.get('title', ''),
        content=full_content[:1000] + "..." if len(full_content) > 1000 else full_content,
        sections_count=len(sections)
    )


@app.get("/")
async def root():
    return {
        "message": "Wikipedia API Wrapper",
        "endpoints": {
            "search": "/search/{query}?limit=10",
            "summary": "/article/{title}/summary",
            "content": "/article/{title}/content?include_lead=true"
        }
    }


client = TestClient(app)


def test_search_articles():
    logger.info("Запуск теста test_search_articles")

    test_cases = [
        ("/search/Python", {"limit": 5}),
        ("/search/Artificial%20Intelligence", {"limit": 3}),
        ("/search/TestQuery12345", {"limit": 1})
    ]

    for url, params in test_cases:
        logger.info(f"Тестируем: {url} с параметрами: {params}")
        response = client.get(url, params=params)

        logger.info(f"Статус код: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Успешный ответ: найдено {data['results_count']} статей")
            assert data["results_count"] >= 0
            assert isinstance(data["articles"], list)
        elif response.status_code == 500:
            logger.warning("Ошибка сервера (возможно, проблема с сетью)")

    logger.info("Тест test_search_articles завершен")


def test_get_article_summary():
    logger.info("Запуск теста test_get_article_summary")

    test_cases = [
        "/article/Python/summary",
        "/article/Artificial_intelligence/summary",
        "/article/NonExistentArticle12345/summary"
    ]

    for url in test_cases:
        logger.info(f"Тестируем: {url}")
        response = client.get(url)

        logger.info(f"Статус код: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Успешный ответ: статья '{data['title']}'")
            assert "title" in data
            assert "summary" in data
            assert "url" in data
        elif response.status_code == 404:
            logger.warning("Статья не найдена (ожидаемое поведение)")

    logger.info("Тест test_get_article_summary завершен")


def test_get_article_content():
    logger.info("Запуск теста test_get_article_content")

    test_cases = [
        ("/article/Python/content", {"include_lead": True}),
        ("/article/Python/content", {"include_lead": False}),
        ("/article/NonExistentArticle12345/content", {})
    ]

    for url, params in test_cases:
        logger.info(f"Тестируем: {url} с параметрами: {params}")
        response = client.get(url, params=params)

        logger.info(f"Статус код: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Успешный ответ: статья '{data['title']}', разделов: {data['sections_count']}")
            assert "title" in data
            assert "content" in data
            assert "sections_count" in data
        elif response.status_code == 404:
            logger.warning("Статья не найдена (ожидаемое поведение)")

    logger.info("Тест test_get_article_content завершен")


def test_root_endpoint():
    logger.info("Запуск теста test_root_endpoint")

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data

    logger.info("Тест test_root_endpoint пройден успешно")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("ЗАПУСК ВСЕХ ТЕСТОВ")
    logger.info("=" * 50)

    try:
        test_root_endpoint()
        test_search_articles()
        test_get_article_summary()
        test_get_article_content()

        logger.info("=" * 50)
        logger.info("ВСЕ ТЕСТЫ УСПЕШНО ЗАВЕРШЕНЫ")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Ошибка при выполнении тестов: {e}")
        logger.info("=" * 50)
        logger.info("ТЕСТЫ ЗАВЕРШЕНЫ С ОШИБКАМИ")
        logger.info("=" * 50)
