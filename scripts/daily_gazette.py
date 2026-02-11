import requests
import datetime
import time
import os
from bs4 import BeautifulSoup
from newspaper import Article, Config

# --- CONFIGURATION ---
# Lab domains get an automatic "Pass"
RESEARCH_LABS = ['openai.com', 'anthropic.com', 'deepmind.google', 'mistral.ai', 'sarvam.ai', 'paperbanana.com']

# Reputable news domains
NEWS_DOMAINS = ['techcrunch.com', 'wired.com', 'theverge.com', 'technologyreview.com', 'arstechnica.com', 'venturebeat.com', 'reuters.com', 'nytimes.com', 'bloomberg.com', 'wsj.com']

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 15

def evaluate_content_quality(text, title, domain):
    text_lower = text.lower()
    
    # 1. Direct Pass for Research Labs
    if any(lab in domain for lab in RESEARCH_LABS):
        return True, 10
    
    # 2. Hard Noise Filter
    noise = ["excited to announce", "hiring for", "joined the team", "my new role", "looking for a job"]
    if any(n in text_lower for n in noise):
        return False, 0

    # 3. Expanded Signal Keywords
    signals = {
        'weights': 3, 'parameters': 3, 'inference': 2, 'latency': 2, 'benchmark': 2,
        'transformer': 2, 'dataset': 2, 'gpu': 1, 'token': 1, 'quantization': 2,
        'fine-tuning': 2, 'architecture': 1, 'llm': 1, 'model': 1, 'training': 1
    }
    
    score = sum(points for word, points in signals.items() if word in text_lower)
    
    # Lowered threshold to 3 for better hit rates
    return (score >= 3), score

def fetch_reputable_ai_news():
    print("🗞️ Scraping for High-Signal News...")
    # Expanded to 72 hours to ensure we get hits
    time_window = int(time.time()) - (72 * 3600)
    
    # Combined query to hit both general AI and specific targets
    url = f"https://hn.algolia.com/api/v1/search_by_date?query=AI&tags=story&numericFilters=created_at_i>{time_window}"
    
    try:
        response = requests.get(url)
        hits = response.json().get('hits', [])
        valid_articles = []
        
        for hit in hits:
            story_url = hit.get('url', '')
            if not story_url: continue
            
            domain = story_url.split('/')[2].replace('www.', '')
            
            # Step 1: Pre-check (Reputable source OR high community interest)
            if any(d in domain for d in (NEWS_DOMAINS + RESEARCH_LABS)) or hit.get('points', 0) > 30:
                article = Article(story_url, config=config)
                try:
                    article.download()
                    article.parse()
                    
                    is_quality, score = evaluate_content_quality(article.text, hit['title'], domain)
                    
                    if is_quality:
                        # Pre-sanitize text to avoid f-string backslash errors
                        clean_body = article.text[:1000].replace('\n', '<br>')
                        valid_articles.append({
                            'title': hit['title'],
                            'url': story_url,
                            'author': hit['author'],
                            'source': domain,
                            'content': clean_body
                        })
                        print(f"    [OK - {score}pts]: {hit['title']}")
                except:
                    continue
            
            if len(valid_articles) >= 5: break
            
        return valid_articles
    except Exception as e:
        print(f"Error: {e}")
        return []

# ... [fetch_arxiv_papers and publish_gazette remain the same as previous fixed version] ...

if __name__ == "__main__":
    news = fetch_reputable_ai_news()
    papers = fetch_arxiv_papers()
    
    # Safety Check: If news is empty, add a placeholder so the site doesn't look broken
    if not news:
        news = [{
            'title': "The Frontier Quietens",
            'url': "#",
            'author': "System",
            'source': "Gemini Gazette",
            'content': "No high-signal stories met the technical threshold today. The research wire remains active below."
        }]
    
    from scripts.daily_gazette import publish_gazette # Or keep the function in the same file
    publish_gazette(news, papers)
