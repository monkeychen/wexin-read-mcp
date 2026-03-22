"""MCP服务器主入口"""

import sys
from pathlib import Path

# 添加src目录到Python路径，支持直接运行
if __name__ == "__main__":
    src_dir = Path(__file__).parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

from fastmcp import FastMCP
import logging

# 支持相对导入和绝对导入
try:
    from .scraper import WeixinScraper
except ImportError:
    from scraper import WeixinScraper

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化MCP服务
mcp = FastMCP("weixin-reader")

# 初始化爬虫（全局单例）
scraper = WeixinScraper()


@mcp.tool()
async def read_weixin_article(url: str) -> dict:
    """
    读取微信公众号文章内容
    
    Args:
        url: 微信文章URL，格式: https://mp.weixin.qq.com/s/xxx
        
    Returns:
        dict: {
            "success": bool,
            "title": str,
            "author": str,
            "publish_time": str,
            "content": str,
            "error": str | None
        }
    """
    try:
        # URL验证
        if not url.startswith("https://mp.weixin.qq.com/s/") and not url.startswith("https://mp.weixin.qq.com/s?"):
            return {
                "success": False,
                "error": "Invalid URL format. Must be a Weixin article URL (https://mp.weixin.qq.com/s/xxx or https://mp.weixin.qq.com/s?xxx)."
            }
        
        logger.info(f"Fetching article: {url}")
        
        # 调用爬虫获取内容
        result = await scraper.fetch_article(url)
        
        if result.get("success"):
            logger.info(f"Successfully fetched: {result.get('title', 'Unknown')}")
        else:
            logger.error(f"Failed to fetch: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching article: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def save_weixin_article_to_pdf(url: str, output_path: str) -> dict:
    """
    将微信公众号文章内容保存为PDF文档（包含图片）
    
    Args:
        url: 微信文章URL，格式: https://mp.weixin.qq.com/s/xxx
        output_path: 保存的本地PDF文件路径，例如: /tmp/article.pdf
        
    Returns:
        dict: {
            "success": bool,
            "title": str,
            "output_path": str,
            "error": str | None
        }
    """
    try:
        # URL验证
        if not url.startswith("https://mp.weixin.qq.com/s/") and not url.startswith("https://mp.weixin.qq.com/s?"):
            return {
                "success": False,
                "error": "Invalid URL format. Must be a Weixin article URL (https://mp.weixin.qq.com/s/xxx or https://mp.weixin.qq.com/s?xxx)."
            }
        
        logger.info(f"Saving article to PDF: {url} -> {output_path}")
        
        # 调用爬虫生成PDF
        result = await scraper.save_to_pdf(url, output_path)
        
        if result.get("success"):
            logger.info(f"Successfully saved PDF: {result.get('title', 'Unknown')} to {output_path}")
        else:
            logger.error(f"Failed to save PDF: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error saving article to PDF: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


# 清理函数
async def cleanup():
    """清理资源"""
    await scraper.cleanup()


if __name__ == "__main__":
    # 启动MCP服务器
    import asyncio
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        asyncio.run(cleanup())

