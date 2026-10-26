#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Spark 静态页面服务入口（仅使用 Python 标准库，无需 pip install）。

同时兼容两类运行方式：
1) WSGI 服务器托管（Gunicorn / uWSGI / 各类强制 main:app 的平台）：
   模块顶层暴露了 app / application / handler 三个 WSGI 可调用对象。
   例如:  gunicorn main:app
2) 直接运行:
   python main.py   -> 用标准库 wsgiref 起服务，端口读环境变量 PORT（默认 8000）

页面访问:
- 根路径 / 会 302 跳转到 /g_spark.html
- 静态图片位于 /images/...
"""

import mimetypes
import os
from urllib.parse import unquote
from wsgiref.simple_server import make_server

# 静态资源根目录 = main.py 所在目录（其下有 g_spark.html 与 images/）
ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "0.0.0.0")
ENTRY_PAGE = "g_spark.html"

mimetypes.add_type("text/html", ".html")
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/jpeg", ".jpeg")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")


def _resolve_fs_path(path_info: str):
    """把 URL 路径映射到磁盘文件，并防止目录穿越。返回绝对路径或 None。"""
    rel = unquote(path_info.lstrip("/"))
    if not rel:
        rel = ENTRY_PAGE
    fs_path = os.path.realpath(os.path.join(ROOT, rel))
    # 必须限制在 ROOT 之内
    if not (fs_path == ROOT or fs_path.startswith(ROOT + os.sep)):
        return None
    return fs_path


def gspark_app(environ, start_response):
    """标准 WSGI 应用：托管 g_spark.html 与 images/ 下的静态资源。"""
    path = environ.get("PATH_INFO", "/")

    # 根路径 / 常见默认首页 -> 跳转到真实入口页
    if path in ("/", "/index.html", "/index.htm"):
        start_response("302 Found", [("Location", "/" + ENTRY_PAGE)])
        return [b""]

    # 健康检查（部分平台会探测 /healthz 或 /health）
    if path in ("/healthz", "/health"):
        start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"ok"]

    fs_path = _resolve_fs_path(path)
    if not fs_path or not os.path.isfile(fs_path):
        start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
        return [b"404 Not Found"]

    try:
        with open(fs_path, "rb") as f:
            body = f.read()
    except OSError:
        start_response("500 Internal Server Error",
                       [("Content-Type", "text/plain; charset=utf-8")])
        return [b"500 Internal Server Error"]

    ctype, _ = mimetypes.guess_type(fs_path)
    headers = [
        ("Content-Type", ctype or "application/octet-stream"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "public, max-age=3600"),
    ]
    start_response("200 OK", headers)
    return [body]


# —— 顶层入口契约：不同平台查找的名字不同，统一指向同一个 WSGI 应用 ——
app = gspark_app
application = gspark_app
handler = gspark_app


if __name__ == "__main__":
    httpd = make_server(HOST, PORT, gspark_app)
    print(f"G-Spark server running at http://{HOST}:{PORT}/{ENTRY_PAGE}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        httpd.server_close()
