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
            with urlopen(url, timeout=8) as response:
                raw = response.read()
            for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
                try:
                    content = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    content = ""
            if not content:
                content = raw.decode("utf-8", errors="ignore")

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
