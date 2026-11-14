import os, base64, json, time, urllib.request
from playwright.sync_api import sync_playwright
TOKEN = os.environ.get('GHPAT',''); REPO='3151677521ycc/hands'
PHONE = os.environ.get('PHONE','17809152045')
def api_get(path):
    try:
        r=urllib.request.urlopen(urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/{path}',
            headers={'Authorization':f'Bearer {TOKEN}','Accept':'application/vnd.github+json'}))
        return base64.b64decode(json.loads(r.read())['content']).decode().strip()
    except Exception:
        return ''
def gh_put(path, data, msg):
    url=f'https://api.github.com/repos/{REPO}/contents/{path}'
    body={'message':msg,'content':base64.b64encode(data).decode()}
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers={'Authorization':f'Bearer {TOKEN}','Accept':'application/vnd.github+json'}))
        body['sha']=json.loads(r.read())['content']['sha']
    except Exception:
        pass
    try:
        urllib.request.urlopen(urllib.request.Request(url,data=json.dumps(body).encode(),method='PUT',
            headers={'Authorization':f'Bearer {TOKEN}','Accept':'application/vnd.github+json','Content-Type':'application/json'}))
        print('committed',path,flush=True)
    except Exception as e:
        print('commit fail',path,e,flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--no-sandbox'])
    ctx=b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',viewport={'width':1280,'height':900})
    pg=ctx.new_page()
    pg.goto('https://www.douyin.com/',wait_until='domcontentloaded',timeout=60000)
    pg.wait_for_timeout(4000)
    for sel in ['text=登录','button:has-text("登录")']:
        try: pg.click(sel,timeout=5000); print('clicked',sel,flush=True); break
        except Exception: pass
    pg.wait_for_timeout(3000)
    for sel in ['text=验证码登录','text=验证码']:
        try: pg.click(sel,timeout=4000); print('tab',sel,flush=True); break
        except Exception: pass
    pg.wait_for_timeout(2000)
    ph=pg.query_selector('input[placeholder*="手机号"]')
    if ph is None: ph=pg.query_selector('input[name="mobile"]')
    if ph is None:
        pg.screenshot(path='/tmp/x.png'); gh_put('login_debug.png',open('/tmp/x.png','rb').read(),'debug no phone input')
        print('NO_PHONE_INPUT',flush=True); b.close(); raise SystemExit(1)
    ph.fill(PHONE); print('phone filled',flush=True)
    pg.wait_for_timeout(500)
    for sel in ['text=获取验证码','text=发送验证码']:
        try: pg.click(sel,timeout=4000); print('clicked code btn',sel,flush=True); break
        except Exception: pass
    gh_put('sms_status.txt','code_requested'.encode(),'sms requested')
    print('WAIT_CODE',flush=True)
    code=''
    for i in range(60):
        code=api_get('sms_code.txt')
        if code: print('got code len',len(code),flush=True); break
        pg.wait_for_timeout(5000)
    if not code:
        pg.screenshot(path='/tmp/t.png'); gh_put('login_debug.png',open('/tmp/t.png','rb').read(),'timeout no code')
        print('NO_CODE_TIMEOUT',flush=True); b.close(); raise SystemExit(1)
    ci=pg.query_selector('input[placeholder*="验证码"]')
    if ci is not None: ci.fill(code); print('code filled',flush=True)
    pg.wait_for_timeout(500)
    for sel in ['button:has-text("登录")','text=登录']:
        try: pg.click(sel,timeout=4000); print('submit',sel,flush=True); break
        except Exception: pass
    pg.wait_for_timeout(6000)
    print('URL',pg.url,flush=True)
    txt=pg.inner_text('body')[:300].replace('\n',' | ')
    print('TEXT',txt,flush=True)
    pg.screenshot(path='/tmp/after.png'); gh_put('login_after.png',open('/tmp/after.png','rb').read(),'after login')
    b.close()
