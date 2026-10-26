#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G-Spark 静态页面服务入口（仅使用 Python 标准库，无需 pip install）。

适用于「强制要求 Python main.py 入口」的托管平台：
- 平台执行:  python main.py
- 默认端口:  读取环境变量 PORT（平台通常会注入），否则回退到 8000
- 监听地址:  0.0.0.0（容器/云平台外部可访问）

访问地址:
- 首页自动跳转到 /g_spark.html
- 也可直接访问 http(s)://<域名>/g_spark.html
"""

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# 静态资源根目录 = main.py 所在目录（其下有 g_spark.html 与 images/）
ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "0.0.0.0")


class GSparkHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 固定从本文件所在目录提供静态文件
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        # 根路径 / 与常见默认首页都跳转到实际页面
        if self.path in ("/", "/index.html", "/index.htm"):
            self.send_response(302)
            self.send_header("Location", "/g_spark.html")
            self.end_headers()
            return
        return super().do_GET()

    def log_message(self, fmt, *args):
        # 简洁的访问日志
        print("[G-Spark] " + (fmt % args))


def main():
    server = ThreadingHTTPServer((HOST, PORT), GSparkHandler)
    print(f"G-Spark server running at http://{HOST}:{PORT}/g_spark.html")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
