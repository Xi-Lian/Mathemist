from .._shared import *


class _DownloadCloudMarkdownMixin:
    def _download_cloud_markdown(self, url: str) -> str:
        """
        下载云端Markdown内容，并做本地缓存
        """
        if not url:
            return ""

        url = self._sanitize_cloud_url(url)

        cache_key = hashlib.md5(url.encode("utf-8")).hexdigest()
        cache_file = self.lesson_plan_cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                return cached.get("content", "")
            except Exception:
                logger.warning(f"读取教案缓存失败，重新下载: {cache_file}")

        try:
            logger.info(f"开始下载云端Markdown: {url}")
            import requests
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            
            # 直接使用response.text，让requests处理编码
            content = response.text
            
            if not content:
                # 如果内容为空，尝试使用content属性
                content = response.content.decode("utf-8", errors="ignore")

            cache_file.write_text(
                json.dumps({"url": url, "content": content}, ensure_ascii=False),
                encoding="utf-8"
            )
            return content
        except (HTTPError, URLError, TimeoutError) as e:
            logger.error(f"下载云端Markdown失败: {url}, 错误: {e}")
            return ""
        except Exception as e:
            logger.error(f"下载云端Markdown异常: {url}, 错误: {e}")
            return ""
