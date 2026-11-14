import os, base64, json, urllib.request
from playwright.sync_api import sync_playwright
TOKEN = os.environ.get('GHPAT',''); REPO = '3151677521ycc/hands'
print('PATLEN', len(TOKEN), flush=True)
def gh_put(path, data, msg):
    url = f'https://api.github.com/repos/{REPO}/contents/{path}'
    body = {'message': msg, 'content': base64.b64encode(data).decode()}
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/vnd.github+json'}))
        body['sha'] = json.loads(r.read())['content']['sha']
        print('got existing sha', flush=True)
    except Exception:
        pass
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method='PUT',
        headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req); print('committed', path, flush=True)
    except Exception as e:
        print('commit fail', path, e, flush=True)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox'])
    ctx = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36', viewport={'width': 1280, 'height': 900})
    pg = ctx.new_page()
    pg.goto('https://www.douyin.com/', wait_until='domcontentloaded', timeout=60000)
    pg.wait_for_timeout(4000)
    for sel in ['text=登录', 'button:has-text("登录")']:
        try:
            pg.click(sel, timeout=5000); print('clicked', sel, flush=True); break
        except Exception:
            pass
    # 等二维码图片真正加载（data:image 且足够大）
    qr = None
    for _ in range(40):
        for el in pg.query_selector_all('img'):
            src = (el.get_attribute('src') or '')
            if src.startswith('data:image'):
                box = el.bounding_box()
                if box and box['width'] > 120 and box['height'] > 120:
                    qr = el
                    break
        if qr is not None:
            break
        pg.wait_for_timeout(1000)
    if qr is not None:
        qr.screenshot(path='/tmp/qr.png')
        shot = open('/tmp/qr.png', 'rb').read()
        print('QR_ELEMENT_OK', flush=True)
    else:
        pg.wait_for_timeout(3000)
        shot = pg.screenshot(full_page=False)
        print('QR_FALLBACK_FULLPAGE', flush=True)
    gh_put('login_qr.png', shot, 'login qr')
    print('QR_SIZE', len(shot), flush=True)
    if os.environ.get('NOWAIT') == '1':
        print('NOWAIT exit', flush=True)
        b.close()
        raise SystemExit(0)
    ok = False
    for i in range(90):
        # 每 45 秒检查二维码是否失效，失效就刷新并重新提交
        if False:  # 关掉自动刷新：换码会让用户扫的那张作废
            try:
                body = pg.inner_text('body')
                if ('失效' in body) or ('刷新' in body):
                    for sel in ['text=刷新', 'text=点击刷新', 'text=刷新二维码']:
                        try:
                            pg.click(sel, timeout=2500); print('refreshed qr', flush=True); break
                        except Exception:
                            pass
                    pg.wait_for_timeout(3000)
                    shot2 = pg.screenshot(full_page=False)
                    gh_put('login_qr.png', shot2, 'login qr refresh')
            except Exception as e:
                print('refresh err', type(e).__name__, flush=True)
        # 每 15 秒重载一次，确保页面反映最新登录态
        if i > 0 and i % 3 == 0:
            try:
                pg.reload(wait_until='domcontentloaded', timeout=30000)
                pg.wait_for_timeout(2000)
                print('reloaded at', i*5, flush=True)
            except Exception as e:
                print('reload err', type(e).__name__, flush=True)
        cs = ctx.cookies()
        if any(c['name'] in ('sessionid', 'sessionid_ss', 'sid_tt') for c in cs):
            ok = True; print('LOGIN_OK_cookie_at', i * 5, 's', flush=True); break
        try:
            has_login = pg.query_selector('button:has-text("登录")') is not None
            if (not has_login) and (pg.query_selector('text=我的') is not None or pg.query_selector('text=发布视频') is not None):
                ok = True; print('LOGIN_OK_dom_at', i * 5, 's', flush=True); break
        except Exception:
            pass
        pg.wait_for_timeout(5000)
    if ok:
        pg.goto('https://www.douyin.com/', wait_until='domcontentloaded', timeout=60000)
        pg.wait_for_timeout(3000)
        print('AFTER_URL', pg.url, flush=True)
        print('AFTER_TEXT', pg.inner_text('body')[:400].replace('\n', ' | '), flush=True)
        gh_put('login_after.png', pg.screenshot(full_page=False), 'after login')
    else:
        print('LOGIN_TIMEOUT', flush=True)
    b.close()
