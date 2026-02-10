import nltk
from nltk.tokenize import word_tokenize

# --- 1. SETUP NLP ASSETS ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# --- 2. THE SIGNAL GATEKEEPER ---
def evaluate_signal_strength(text, title):
    """
    Returns True if the content is technical/substantive news.
    Returns False if it is a job announcement, fluff, or low-value social post.
    """
    text_lower = text.lower()
    title_lower = title.lower()
    
    # 🛑 THE NOISE LIST (Instant Rejection)
    noise_patterns = [
        "excited to announce", "honored to join", "my new role", 
        "looking for a new", "hiring for", "thanks for the opportunity",
        "personal news", "happy to share that i"
    ]
    if any(p in text_lower for p in noise_patterns):
        return False

    # 🔬 THE SIGNAL LIST (Technical Indicators)
    technical_keywords = [
        'benchmarks', 'transformer', 'inference', 'latency', 'open-source',
        'parameters', 'weights', 'architecture', 'token', 'quantization',
        'fine-tune', 'deployment', 'api', 'state-of-the-art', 'sota'
    ]
    
    # Count how many technical terms appear
    signal_count = sum(1 for word in technical_keywords if word in text_lower)
    
    # Threshold: Must have at least 2 technical terms OR be from a research domain
    if signal_count >= 2:
        return True
    
    # If it's a very short text with no technical terms, it's likely fluff
    if len(text.split()) < 150:
        return False

    return True

# --- 3. UPDATED NEWS FETCHER ---
def fetch_high_signal_news():
    print("🗞️ Scrutinizing the headlines for true signal...")
    url = "https://hn.algolia.com/api/v1/search?query=artificial+intelligence&tags=story&numericFilters=points>20"
    
    try:
        response = requests.get(url)
        hits = response.json().get('hits', [])
        valid_articles = []
        
        for hit in hits:
            # First layer: Basic domain check
            story_url = hit.get('url', '')
            if not story_url: continue

            # Second layer: Deep Content Analysis
            article = Article(story_url, config=config)
            try:
                article.download()
                article.parse()
                
                # THE BIG TEST: Read the article and judge it
                if evaluate_signal_strength(article.text, hit['title']):
                    print(f"    [VERIFIED]: {hit['title']}")
                    valid_articles.append({
                        'title': hit['title'],
                        'url': story_url,
                        'author': hit['author'],
                        'source': story_url.split('/')[2].replace('www.', ''),
                        'content': article.text
                    })
                else:
                    print(f"    [REJECTED - FLUFF]: {hit['title']}")

            except Exception as e:
                continue

            if len(valid_articles) >= 5: break
            
        return valid_articles
    except Exception as e:
        print(f"Error: {e}")
        return []
