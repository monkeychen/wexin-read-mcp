"""Playwright浏览器爬虫"""

from playwright.async_api import async_playwright, Browser, BrowserContext

# 支持相对导入和绝对导入
try:
    from .parser import WeixinParser
except ImportError:
    from parser import WeixinParser


class WeixinScraper:
    """微信文章爬虫"""
    
    def __init__(self):
        self.parser = WeixinParser()
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
    
    async def initialize(self):
        """初始化浏览器"""
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                ]
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
    
    async def fetch_article(self, url: str) -> dict:
        """
        获取微信文章内容
        
        Args:
            url: 文章URL
            
        Returns:
            dict: 包含文章数据的字典
        """
        try:
            await self.initialize()
            
            # 创建新页面
            page = await self.context.new_page()
            
            try:
                # 访问URL，等待网络空闲
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # 等待关键元素加载
                await page.wait_for_selector('#js_content', timeout=10000)
                
                # 获取页面HTML
                html_content = await page.content()
                
                # 解析内容
                result = self.parser.parse(html_content, url)
                
                return {
                    "success": True,
                    **result,
                    "error": None
                }
            finally:
                # 确保页面关闭
                await page.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch article: {str(e)}"
            }

    async def save_to_pdf(self, url: str, output_path: str) -> dict:
        """
        将微信文章保存为PDF（包含图片）
        
        Args:
            url: 文章URL
            output_path: PDF保存路径
            
        Returns:
            dict: 包含执行结果的字典
        """
        try:
            await self.initialize()
            
            # 创建新页面
            page = await self.context.new_page()
            
            try:
                # 访问URL，等待网络空闲
                await page.goto(url, wait_until='networkidle', timeout=30000)
                
                # 等待关键元素加载
                await page.wait_for_selector('#js_content', timeout=10000)

                # 提取标题用于返回
                title = await page.title()
                
                # 滚动到底部以加载所有懒加载图片
                await page.evaluate('''async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;

                            if(totalHeight >= scrollHeight - window.innerHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }''')
                
                # 等待图片加载完成
                await page.wait_for_timeout(2000)

                # 隐藏一些不需要的元素，如顶部导航、底部评论区等（可选）
                await page.evaluate('''() => {
                    const elementsToHide = document.querySelectorAll('.qr_code_pc_outer, #js_pc_qr_code, .rich_media_area_extra');
                    elementsToHide.forEach(el => el.style.display = 'none');
                }''')
                
                # 生成PDF
                await page.pdf(
                    path=output_path,
                    format='A4',
                    print_background=True,
                    margin={'top': '20px', 'right': '20px', 'bottom': '20px', 'left': '20px'}
                )
                
                return {
                    "success": True,
                    "title": title,
                    "output_path": output_path,
                    "error": None
                }
            finally:
                # 确保页面关闭
                await page.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save PDF: {str(e)}"
            }
    
    async def cleanup(self):
        """清理资源"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

