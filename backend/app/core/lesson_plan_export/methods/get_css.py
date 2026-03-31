from .._shared import *


class _GetCssMixin:
    def _get_css(self) -> str:
        """获取CSS样式"""
        return """<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    body {
        font-family: "Microsoft YaHei", "SimSun", sans-serif;
        line-height: 1.8;
        color: #333;
        background-color: #f5f5f5;
        padding: 20px;
    }
    .container {
        max-width: 900px;
        margin: 0 auto;
        background-color: white;
        padding: 40px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-radius: 8px;
    }
    h1 {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 30px;
        padding-bottom: 15px;
        border-bottom: 2px solid #3498db;
    }
    h2 {
        color: #34495e;
        margin-top: 30px;
        margin-bottom: 15px;
        padding-left: 10px;
        border-left: 4px solid #3498db;
    }
    h3 {
        color: #555;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    p {
        margin-bottom: 15px;
        text-align: justify;
    }
    ul, ol {
        margin-left: 30px;
        margin-bottom: 15px;
    }
    li {
        margin-bottom: 8px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: left;
    }
    th {
        background-color: #3498db;
        color: white;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    tr:hover {
        background-color: #f5f5f5;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: "Courier New", monospace;
    }
    pre {
        background-color: #f4f4f4;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
        margin: 15px 0;
    }
    blockquote {
        border-left: 4px solid #3498db;
        padding-left: 20px;
        margin: 20px 0;
        color: #666;
        font-style: italic;
    }
    @media print {
        body {
            background-color: white;
            padding: 0;
        }
        .container {
            box-shadow: none;
            padding: 20px;
        }
    }
</style>"""
