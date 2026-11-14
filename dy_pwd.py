import os, base64, json, urllib.request
from playwright.sync_api import sync_playwright
TOKEN=os.environ.get('GHPAT',''); REPO='3151677521ycc/hands'
PHONE=os.environ.get('PHONE','17809152045')
PWD_=os.environ.get('DYPWD','')
def gh_put(path,data,msg):
    url=f'https://api.github.com/repos/{REPO}/contents/{path}'
    body={'message':msg,'content':base64.b64encode(data).decode()}
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':f'Bearer {TOKEN}','Accept':'application/vnd.github+json'}))
        body['sha']=json.loads(r.read())['content']['sha']
    except Exception: pass
    try:
        urllib.request.urlopen(urllib.request.Request(url,data=json.dumps(body).encode(),method='PUT',
            headers={'Authorization':f'Bearer {TOKEN}','Accept':'application/vnd.github+json','Content-Type':'application/json'}))
        print('committed',path,flush=True)
    except Exception as e: print('commit fail',path,e,flush=True)
def shot(pg,name):
    p='/tmp/'+name; pg.screenshot(path=p); gh_put(name,open(p,'rb').read(),name)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--no-sandbox'])
    ctx=b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',viewport={'width':1280,'height':900})
    pg=ctx.new_page()
    pg.goto('https://www.douyin.com/',wait_until='domcontentloaded',timeout=60000)
    pg.wait_for_timeout(4000)
    for sel in ['text=登录','button:has-text("登录")']:
        try: pg.click(sel,timeout=5000); print('open login',flush=True); break
        except Exception: pass
    pg.wait_for_timeout(2500)
    for sel in ['text=密码登录']:
        try: pg.click(sel,timeout=4000); print('tab pwd',flush=True); break
        except Exception: print('no pwd tab',flush=True)
    pg.wait_for_timeout(1500)
    # 选国家码 +86（按坐标点，DOM 里抓不到）
    pg.mouse.click(712, 396)
    pg.wait_for_timeout(1800)
    shot(pg, 'country_open.png')
    picked = False
    for opt in ['+86', '中国大陆', 'China', '中国']:
        try:
            pg.click(f'text={opt}', timeout=2500)
            print('country picked', opt, flush=True)
            picked = True
            break
        except Exception:
            pass
    if not picked:
        print('country NOT picked', flush=True)
    pg.wait_for_timeout(800)
    # 填手机号
    ph=pg.query_selector('input[placeholder*="手机号"]')
    pw=pg.query_selector('input[type="password"]') or pg.query_selector('input[placeholder*="密码"]')
    print('phone_input', bool(ph), 'pwd_input', bool(pw), flush=True)
    if ph: ph.fill(PHONE)
    if pw: pw.fill(PWD_)
    pg.wait_for_timeout(800)
    shot(pg,'login_pre.png')
    # 点弹窗里的「登录」按钮（坐标，避免点到页面右上角那个）
    if pw: pw.press('Enter')
    print('pressed Enter', flush=True)
    pg.wait_for_timeout(2500)
    pg.mouse.click(819, 585)
    print('also clicked submit', flush=True)
    pg.wait_for_timeout(8000)
    print('URL',pg.url,flush=True)
    t=pg.inner_text('body')
    print('TEXT',t[:400].replace('\n',' | '),flush=True)
    shot(pg,'login_after.png')
    # 是否出现滑块
    if '拖动' in t or '滑块' in t or '验证' in t:
        print('CAPTCHA_MAYBE',flush=True)
    b.close()
