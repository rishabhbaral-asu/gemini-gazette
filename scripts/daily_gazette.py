import requests
import datetime
import re
from bs4 import BeautifulSoup

def fetch_arxiv_research():
    # 1. DATE CALCULATION (Last 7 Days)
    today = datetime.datetime.now()
    seven_days_ago = today - datetime.timedelta(days=7)
    
    # ArXiv expects format: YYYYMMDDHHMM
    date_format = "%Y%m%d0000"
    start_str = seven_days_ago.strftime(date_format)
    end_str = today.strftime(date_format)
    
    print(f"🔬 Scoping papers from {seven_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}...")
    
    # 2. QUERY CONSTRUCTION
    # We fetch more results (500) to ensure we cover the full week of high-volume categories
    # Query: (Categories) AND (Date Range)
    base_query = "cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.CV"
    date_query = f"submittedDate:[{start_str}+TO+{end_str}]"
    final_query = f"({base_query})+AND+{date_query}"
    
    url = f"https://export.arxiv.org/api/query?search_query={final_query}&sortBy=submittedDate&sortOrder=descending&max_results=500"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    sections = {'AI & REINFORCEMENT': [], 'NLP & LANGUAGE': [], 'VISION & MULTIMODAL': []}
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, 'xml')
        entries = soup.find_all('entry')
        
        print(f"   ↳ Found {len(entries)} papers. sorting by priority...")

        for entry in entries:
            primary_cat = entry.find('arxiv:primary_category')['term']
            title = entry.title.text.strip().replace('\n', ' ')
            summary = entry.summary.text.strip().replace('\n', ' ')
            
            paper = {
                'title': title,
                'summary': summary,
                'link': entry.id.text.strip(),
                'authors': [a.find('name').text for a in entry.find_all('author')][:2],
                'date': entry.published.text[:10],
                'priority_score': calculate_priority(title, summary)
            }
            
            # Map ArXiv categories to your "Desks"
            if primary_cat == 'cs.CL':
                sections['NLP & LANGUAGE'].append(paper)
            elif primary_cat == 'cs.CV':
                sections['VISION & MULTIMODAL'].append(paper)
            else:
                sections['AI & REINFORCEMENT'].append(paper)
        
        # 3. SORTING BY PRIORITY
        # Sort each section: High priority score first, then by date (descending)
        for key in sections:
            sections[key].sort(key=lambda x: (x['priority_score'], x['date']), reverse=True)
            
        return sections

    except Exception as e:
        print(f"Error: {e}")
        return {}

def calculate_priority(title, summary):
    """
    Assigns a score to papers based on keywords. 
    High score = Agents, World Models, Reasoning.
    """
    text = (title + " " + summary).lower()
    score = 0
    
    # Tier 1: The "Must Haves" (Agents & World Models)
    high_priority = ['world model', 'autonomous agent', 'generative agent', 'agentic', 'multi-agent']
    if any(k in text for k in high_priority):
        score += 10
        
    # Tier 2: Strong signals
    medium_priority = ['reasoning', 'planning', 'chain of thought', 'reinforcement learning', 'policy']
    if any(k in text for k in medium_priority):
        score += 5

    return score

def publish_sectioned_gazette(sections):
    today = datetime.datetime.now().strftime("%B %d, %Y").upper()
    
    sections_html = ""
    accent_map = {
        'AI & REINFORCEMENT': 'ai-accent',
        'NLP & LANGUAGE': 'nlp-accent',
        'VISION & MULTIMODAL': 'vision-accent'
    }

    for name, papers in sections.items():
        if not papers: continue
        
        paper_cards = ""
        # Increased display limit to 30 per section
        for p in papers[:30]: 
            accent = accent_map.get(name, '')
            
            # Add a visual indicator for high priority papers
            icon = ""
            if p['priority_score'] >= 10:
                icon = "🔥 " # Fire for agents/world models
            elif p['priority_score'] >= 5:
                icon = "⚡ " # Bolt for reasoning/planning
            
            paper_cards += f"""
            <div class="card {accent}">
                <div class="card-date">{p['date']}</div>
                <h3><a href="{p['link']}" target="_blank">{icon}{p['title']}</a></h3>
                <p class="meta">By {", ".join(p['authors'])}</p>
                <p class="text">{p['summary'][:280]}...</p>
            </div>
            """
        
        sections_html += f"""
        <section class="news-desk">
            <h2 class="desk-title">{name} DESK <span>{len(papers)} PAPERS THIS WEEK</span></h2>
            <div class="horizontal-scroll">
                {paper_cards}
            </div>
        </section>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>The Silicon Scroll | Weekly Research</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Libre+Baskerville:wght@400;700&display=swap');
            
            body {{ background: #f4f1ea; color: #1a1a1a; font-family: 'Libre Baskerville', serif; margin: 0; padding: 2vw; }}
            .masthead {{ text-align: center; border-bottom: 5px double #333; margin-bottom: 40px; padding-bottom: 15px; }}
            .masthead h1 {{ font-family: 'Playfair Display'; font-size: 5rem; margin: 0; letter-spacing: -2px; }}
            
            .news-desk {{ margin-bottom: 50px; }}
            .desk-title {{ 
                border-bottom: 2px solid #333; 
                font-family: 'Playfair Display'; 
                font-size: 1.8rem; 
                margin-bottom: 15px; 
                padding-bottom: 5px; 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
            }}
            .desk-title span {{ font-size: 0.7rem; font-family: 'Libre Baskerville'; opacity: 0.5; }}
            
            .horizontal-scroll {{ 
                display: flex; 
                overflow-x: auto; 
                gap: 25px; 
                padding-bottom: 20px;
                scrollbar-width: thin;
                scrollbar-color: #333 #f4f1ea;
            }}
            
            .horizontal-scroll::-webkit-scrollbar {{ height: 8px; }}
            .horizontal-scroll::-webkit-scrollbar-thumb {{ background: #333; border-radius: 4px; }}

            .card {{ 
                flex: 0 0 350px; 
                background: #fffefc; 
                border: 1px solid #d1cec1; 
                padding: 25px; 
                box-shadow: 4px 4px 0px rgba(0,0,0,0.05);
                transition: transform 0.2s;
                display: flex;
                flex-direction: column;
            }}
            .card:hover {{ transform: translateY(-5px); }}
            
            .card-date {{ font-size: 10px; font-weight: bold; color: #777; margin-bottom: 10px; }}
            h3 {{ font-family: 'Playfair Display'; font-size: 1.3rem; margin: 0 0 10px 0; line-height: 1.2; }}
            h3 a {{ color: #1a1a1a; text-decoration: none; }}
            .meta {{ font-size: 11px; font-weight: bold; text-transform: uppercase; color: #555; margin-bottom: 10px; display: block; }}
            .text {{ font-size: 13px; line-height: 1.6; color: #333; flex-grow: 1; }}

            .ai-accent {{ border-top: 6px solid #2c3e50; }}
            .nlp-accent {{ border-top: 6px solid #27ae60; }}
            .vision-accent {{ border-top: 6px solid #e67e22; }}
        </style>
    </head>
    <body>
        <div class="masthead">
            <div style="font-size: 50px; margin-bottom: 10px;">🦉</div>
            <h1>The Silicon Scroll</h1>
            <p>TEMPE, AZ — {today} — WEEKLY INTELLIGENCE</p>
        </div>
        {sections_html}
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Gazette published: The Silicon Scroll is ready.")

if __name__ == "__main__":
    data = fetch_arxiv_research()
    publish_sectioned_gazette(data)
