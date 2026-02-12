import requests
import datetime
from bs4 import BeautifulSoup

def fetch_arxiv_research(limit=60): # Fetch more to ensure we fill all 3 sections
    print(f"🔬 Scoping {limit} papers across AI, CL, and CV...")
    url = f"https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.CV&sortBy=submittedDate&sortOrder=descending&max_results={limit}"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    sections = {'AI': [], 'NLP': [], 'VISION': []}
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.content, 'xml')
        entries = soup.find_all('entry')
        
        for entry in entries:
            primary_cat = entry.find('arxiv:primary_category')['term']
            paper = {
                'title': entry.title.text.strip().replace('\n', ' '),
                'summary': entry.summary.text.strip().replace('\n', ' '),
                'link': entry.id.text.strip(),
                'authors': [a.find('name').text for a in entry.find_all('author')][:2],
                'date': entry.published.text[:10]
            }
            
            # Categorize into sections
            if primary_cat == 'cs.CL':
                sections['NLP'].append(paper)
            elif primary_cat == 'cs.CV':
                sections['VISION'].append(paper)
            else:
                sections['AI'].append(paper)
                
        return sections
    except Exception as e:
        print(f"Error: {e}")
        return {}

def publish_sectioned_gazette(sections):
    today = datetime.datetime.now().strftime("%B %d, %Y").upper()
    
    sections_html = ""
    for name, papers in sections.items():
        if not papers: continue
        
        paper_cards = ""
        for p in papers[:15]: # Limit to top 15 per scrollable row
            paper_cards += f"""
            <div class="card">
                <div class="card-date">{p['date']}</div>
                <h3><a href="{p['link']}" target="_blank">{p['title']}</a></h3>
                <p class="meta">By {", ".join(p['authors'])}</p>
                <p class="text">{p['summary'][:280]}...</p>
            </div>
            """
        
        sections_html += f"""
        <section class="news-desk">
            <h2 class="desk-title">{name} DESK</h2>
            <div class="horizontal-scroll">
                {paper_cards}
            </div>
        </section>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Libre+Baskerville:wght@400;700&display=swap');
            
            body {{ background: #f4f1ea; color: #1a1a1a; font-family: 'Libre Baskerville', serif; margin: 0; padding: 2vw; }}
            .masthead {{ text-align: center; border-bottom: 5px double #333; margin-bottom: 40px; }}
            .masthead h1 {{ font-family: 'Playfair Display'; font-size: 5rem; margin: 0; letter-spacing: -2px; }}
            
            .news-desk {{ margin-bottom: 50px; }}
            .desk-title {{ border-bottom: 2px solid #333; font-family: 'Playfair Display'; font-size: 1.8rem; margin-bottom: 15px; padding-bottom: 5px; }}
            
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
                padding: 20px; 
                box-shadow: 2px 2px 0px rgba(0,0,0,0.05);
            }}
            
            .card-date {{ font-size: 10px; font-weight: bold; color: #777; margin-bottom: 10px; }}
            h3 {{ font-family: 'Playfair Display'; font-size: 1.3rem; margin: 0 0 10px 0; line-height: 1.2; }}
            h3 a {{ color: #1a1a1a; text-decoration: none; }}
            .meta {{ font-size: 11px; font-weight: bold; text-transform: uppercase; color: #555; }}
            .text {{ font-size: 13px; line-height: 1.6; color: #333; }}
        </style>
    </head>
    <body>
        <div class="masthead">
            <h1>The Research Gazette</h1>
            <p>TEMPE, AZ — {today} — LATEST SUBMISSIONS</p>
        </div>
        {sections_html}
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ Gazette published with scrollable sections.")

if __name__ == "__main__":
    data = fetch_arxiv_research()
    publish_sectioned_gazette(data)
