import json, re, html, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = [
 ('BBC World','עולם','https://feeds.bbci.co.uk/news/world/rss.xml'),
 ('BBC Technology','עולם','https://feeds.bbci.co.uk/news/technology/rss.xml'),
 ('NPR Music','אלבומים וסינגלים','https://feeds.npr.org/1039/rss.xml'),
 ('Pitchfork','אלבומים וסינגלים','https://pitchfork.com/rss/news/'),
 ('Resident Advisor','תעשיית מוזיקה','https://ra.co/xml/rss.xml'),
 ('The Guardian Culture','אמנות','https://www.theguardian.com/culture/rss'),
 ('The Guardian Books','ספרים','https://www.theguardian.com/books/rss'),
 ('The Guardian Business','עסקים','https://www.theguardian.com/uk/business/rss'),
 ('כאן חדשות','ישראל','https://www.kan.org.il/rss/'),
]

def clean(value):
    value = re.sub(r'<[^>]+>', ' ', value or '')
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()[:550]

def local(el, name):
    for child in el:
        if child.tag.rsplit('}',1)[-1] == name:
            return (child.text or '').strip()
    return ''

def extract(body, source, category):
    root = ET.fromstring(body)
    entries = [e for e in root.iter() if e.tag.rsplit('}',1)[-1] in ('item','entry')]
    out = []
    for e in entries[:30]:
        title = clean(local(e,'title'))
        link = local(e,'link')
        if not link:
            for c in e:
                if c.tag.rsplit('}',1)[-1]=='link' and c.attrib.get('href'):
                    link=c.attrib['href']; break
        summary=clean(local(e,'description') or local(e,'summary') or local(e,'content'))
        if not title or not link.startswith(('https://','http://')): continue
        out.append({'title':title,'link':link,'summary':summary,'source':source,'category':category})
    return out

old_path=Path('news.json')
try: old=json.loads(old_path.read_text(encoding='utf-8'))
except (OSError,ValueError): old=[]
collected=[]
for source,category,url in FEEDS:
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'PersonalNewsPortal/1.0 (+RSS reader)'})
        with urllib.request.urlopen(req,timeout=15) as response:
            articles=extract(response.read(3_000_000),source,category)
        print(source,len(articles)); collected+=articles
    except Exception as exc:
        print('SKIPPED',source,str(exc)[:160])
# Preserve previous headlines when individual feeds are temporarily unavailable.
seen=set(); result=[]
for item in collected+old:
    url=item.get('link','')
    if not url or url in seen: continue
    seen.add(url); result.append(item)
    if len(result)>=250:break
old_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Saved',len(result),'articles at',datetime.now(timezone.utc).isoformat())
