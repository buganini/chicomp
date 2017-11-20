import os
from aiohttp import web

from bsdconv import Bsdconv

index_html = os.path.join(os.path.dirname(__file__), "index.html")
images_folder = os.path.join(os.path.dirname(__file__), "images")

async def index_handler(request):
    r = web.FileResponse(index_html)
    r.content_type = "text/html"
    return r

async def list_handler(request):
    l = [os.path.splitext(x)[0] for x in os.listdir(images_folder)]
    l.sort(key=lambda x:(len(x), x))
    return web.json_response(l)

async def decomp_handler(request):
    c = Bsdconv("utf-8:zh-decomp:split:bsdconv-keyword,bsdconv")
    a = c.conv(request.GET["q"]).decode("utf-8").split(",")
    return web.json_response(a)

async def comp_handler(request):
    c = Bsdconv("bsdconv:zh-comp:utf-8")
    r = c.conv(request.GET["q"]).decode("utf-8")
    return web.json_response({"result":r})

async def info_handler(request):
    cv = Bsdconv("utf-8:cns11643:bsdconv")
    us = list(request.GET["q"])
    cs = [cv.conv(x).decode("utf-8") for x in us]
    r = [{"u":u,"p":c[2:4].lstrip('0'),"c":c[4:]} for u,c in zip(us, cs)]
    return web.json_response(r)

app = web.Application()
app.router.add_get('/', index_handler)
app.router.add_get('/list', list_handler)
app.router.add_get('/decomp', decomp_handler)
app.router.add_get('/comp', comp_handler)
app.router.add_get('/info', info_handler)
app.router.add_static('/images', images_folder)

web.run_app(app)
