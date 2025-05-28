import datetime
from typing import List, Dict, Optional, Union
import logging

from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import requests


# ====== Configuration ======
DATE_FORMAT = "%Y.%m.%d"


# ====== Logging Configuration ======
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def parse_date(text: str) -> Optional[datetime.datetime]:
    """Parse date from text in the format 'YYYY.MM.DD'.
    Given text should be in the format 'YYYY-MM-DD HH:MM:SS'."""
    try:
        dt = text.split()[0]
        return datetime.datetime.strptime(dt, DATE_FORMAT)
    except ValueError:
        return None


def make_url_for_article(gallery_type: str, gallery_id: str, gall_no: int) -> str:
        """Constructs the URL for the article based on gallery type and number."""
        if gallery_type == 'main':
            return f"https://gall.dcinside.com/board/view/?id={gallery_id}&no={gall_no}"
        elif gallery_type == 'minor':
            return f"https://gall.dcinside.com/mgallery/board/view/?id={gallery_id}&no={gall_no}"
        elif gallery_type == 'mini':
            return f"https://gall.dcinside.com/mini/board/view/?id={gallery_id}&no={gall_no}"
        else:
            raise ValueError("Invalid gallery type. Must be 'main', 'minor', or 'mini'.")


@dataclass
class ArticleExceptComment:
    gall_no: int
    date: datetime.datetime
    header: str
    title: str
    view_count: int
    content: str
    recommend_count: int
    nonrecommend_count: int


@dataclass
class ArticleData(ArticleExceptComment):
    """ArticleData extends ArticleExceptComment by adding comments field.
    
    comments structure example:
    [
        {
            "text": "할아버지 제발 여기서 어떡하면좋을까요 야엘티사요ㅡㅡ??",
            "replies": ["안사 꺼져", "어허이런쌰갸지읍는쉐이끼  - dc App"]
        }
    ]
    """
    comments: List[Dict[str, Union[str, List[str]]]]


"""Class for processing DCInside articles"""
class DCArticleProcessor:
    def __init__(self,
                 gallery_id: str,
                 gall_type: str, # 'main', 'minor', or 'mini'
                 gall_no: int,
                 headers: Dict[str, str] = None,
                 is_crawl_comments: bool = True,
                 refresh_time_for_comment: float = 0.5,
                 driver: webdriver.Chrome = None):

        self.gallery_id = gallery_id
        self.gall_type = gall_type
        self.gall_no = gall_no
        self.headers = headers
        if self.headers is None:
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        
        self.refresh_time_for_comment = refresh_time_for_comment
        self.driver = driver
        self.is_crawl_comments = is_crawl_comments
        
    def crawl_except_comment(self) -> Optional[ArticleExceptComment]:
        """Crawl article data except comments."""
        try:
            data = requests.get(make_url_for_article(self.gall_type, self.gallery_id, self.gall_no), headers=self.headers)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch article data {self.gall_no}: {e}")
            return None
        
        soup = BeautifulSoup(data.text, 'html.parser')
        
        # Written date of the article
        try:
            date = soup.select_one('#container > section > article:nth-child(3) > div.view_content_wrap > header > div > div > div.fl > span.gall_date').text
        except AttributeError:
            logger.info(f"Article {self.gall_no} deleted. Skipping...")
            return None
        date = parse_date(date)
        
        # header of the article. e.g. [일반]
        try:
            article_header = soup.select_one('#container > section > article:nth-child(3) > div.view_content_wrap > header > div > h3 > span.title_headtext').text
            article_header = article_header.replace('[', '').replace(']', '')
        except AttributeError:
            article_header = ""
        
        # title of the article
        title = soup.select_one('#container > section > article:nth-child(3) > div.view_content_wrap > header > div > h3 > span.title_subject').text
        
        try:
            content = soup.select_one('#container > section > article:nth-child(3) > div.view_content_wrap > div > div.inner.clear > div.writing_view_box > div.write_div').text
            content = content.rstrip()
            content = content.lstrip()
            content = content.replace('- dc official App', '')
        except AttributeError:
            # No content in article
            content = ""
        
        recommend = soup.select_one(f'#recommend_view_up_{self.gall_no}').text
        nonrecommend = soup.select_one(f'#recommend_view_down_{self.gall_no}').text
        view_count = soup.select_one('#container > section > article:nth-child(3) > div.view_content_wrap > header > div > div > div.fr > span.gall_count').text.split(' ')[1]

        return ArticleExceptComment(
            gall_no=self.gall_no,
            date=date,
            header=article_header,
            title=title,
            content=content,
            view_count=view_count,
            recommend_count=recommend,
            nonrecommend_count=nonrecommend
        )
    
    def crawl_comments(self) -> Optional[List[Dict[str, Union[str, List[str]]]]]:
        """Crawl comments from the article."""
        url = make_url_for_article(self.gall_type, self.gallery_id, self.gall_no)
        self.driver.get(url)
        
        try:
            WebDriverWait(self.driver, self.refresh_time_for_comment).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.cmt_list li[id^='comment_li_'] p.usertxt.ub-word"))
            )
        except TimeoutException:
            # Try to refresh the page if comments are not loaded
            # There are two cases:
            # 1. Comments are not loaded yet
            # 2. There are no comments in article
            try:
                self.driver.refresh()
                WebDriverWait(self.driver, self.refresh_time_for_comment).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.cmt_list li[id^='comment_li_'] p.usertxt.ub-word"))
                )
            except TimeoutException:
                # Assume no comments in article
                logger.info(f"No comments found in article {self.gall_no}.")
                return []
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        comments = []
        
        try:
            for top_li in soup.select("ul.cmt_list.add > li[id^='comment_li_']"):
                cid = top_li["id"].split("_")[-1]

                p = top_li.select_one("p.usertxt.ub-word")
                text = p.get_text(strip=True) if p else ""
                if text == "":
                    # Comment is dccon or image, skip it
                    continue
                text = text.replace('- dc official App', '')

                next_li = top_li.find_next_sibling("li")
                replies = []
                if next_li:
                    reply_ul = next_li.select_one(f"ul.reply_list#reply_list_{cid}")
                    if reply_ul:
                        for reply_li in reply_ul.select("li[id^='reply_li_']"):
                            rp = reply_li.select_one("p.usertxt.ub-word")
                            rtext = rp.get_text(strip=True) if rp else ""
                            if rtext == "":
                                # Reply is dccon or image, skip it
                                continue
                            rtext = rtext.replace('- dc official App', '')
                            replies.append(rtext)

                comments.append({
                    "text": text,
                    "replies": replies
                })
            return comments
        except Exception as e:
            logger.error(f"Error while parsing comments: {e}")
            return None
    
    def process_article(self) -> Optional[ArticleData]:
        """Process the article and return ArticleData."""
        article_data = self.crawl_except_comment()
        if article_data is None:
            # Error occurred while crawling article data
            return None

        if self.is_crawl_comments is True:
            comments = self.crawl_comments()
            if comments is None:
                # Error occurred while crawling comments
                # If there are no comments, comments = []
                return None
        else:
            comments = []
        
        return ArticleData(
            gall_no=article_data.gall_no,
            date=article_data.date,
            header=article_data.header,
            title=article_data.title,
            content=article_data.content,
            view_count=article_data.view_count,
            recommend_count=article_data.recommend_count,
            nonrecommend_count=article_data.nonrecommend_count,
            comments=comments
        )
