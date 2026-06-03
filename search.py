# search.py
import requests

def web_search(query, max_results=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    url = "https://searx.be/search"
    params = {
        "q": query,
        "format": "json",
        "categories": "general",
        "language": "en"
    }
    
    try:
        print(f"🔍 Searching: {query}")
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            return None
        
        formatted = f"🔎 **Search results for '{query}':**\n\n"
        for i, item in enumerate(results[:max_results], 1):
            title = item.get('title', 'No title')
            content = item.get('content', 'No description')[:300]
            url_result = item.get('url', '#')
            formatted += f"{i}. **{title}**\n   {content}\n   📎 Source: {url_result}\n\n"
        
        return formatted
    except Exception as e:
        print(f"Search error: {e}")
        return None

def needs_web_search(prompt):
    keywords = [
        'who is', 'what is', 'when did', 'where is', 'how to',
        'کیست', 'چیست', 'کجاست', 'چگونه', 'اخبار', 'خبر',
        'news', 'latest', 'today', 'weather', 'آب و هوا',
        'alan turing', 'bill gates', 'elon musk', 'president'
    ]
    prompt_lower = prompt.lower()
    return any(k in prompt_lower for k in keywords)
