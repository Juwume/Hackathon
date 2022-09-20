#import mongoengine
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from fake_useragent import UserAgent
import json
from rss_parser import Parser
from xml.etree import ElementTree as ET
from ..models.vc import ArticleVC


async def download_vc_articles():
    """
    Function to parse vc.ru
    Services:
        services
        finance
        life
        marketing
        design
        tech
        hr
        tribuna
    They all can be parsed through the rss feed - https://vc.ru/rss/<service_name>

    :return:
    """
    res = []
    services = {
        'services',
        'finance',
        'life',
        'marketing',
        'design',
        'tech',
        'hr',
        'tribuna'
    }
    async with aiohttp.ClientSession() as session:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user_agent": UserAgent()['google chrome']
        }
        for service in services:
            url = 'https://vc.ru/rss/' + service
            async with session.get(url=url, headers=headers) as response:
                response_text = await response.text()
                # print(response_text)
                print('-------------')
                xml = Parser(response_text).parse()
                for post in xml.feed:
                    url_post = post.link
                    print(url_post)
                    async with session.get(url=url_post, headers=headers) as response_post:
                        response_post_text = await response_post.text()
                        soup = BeautifulSoup(response_post_text, 'lxml')
                        title = soup.title.string
                        paragraphs = soup.find("div", class_='content content--full').find_all("div",
                                                                                  class_="l-island-a")
                        footer = soup.find('div', class_='content-footer content-footer--full l-island-a')
                        repost_amt = int(footer.find('div',class_='v-repost__counter').get_text())
                        comment_amt = int(footer.find('span', class_='comments_counter__count__value').get_text())
                        category = soup.find('div', class_='content-header-author__name')
                        text = ' '.join([paragraph.strip() for paragraph in paragraphs])
                        hash_tags = paragraphs[-2].get_text().strip()
                        print(hash_tags)
                        if '#' not in hash_tags:
                            hash_tags = ''
                        hash_tags = hash_tags.replace('#', '').split()
                        timestamp = soup.find('time', class_='l-hidden lm-inline').get('title')
                        res.append(
                            ArticleVC(
                                title=title,
                                text=text,
                                tags=hash_tags,
                                category=category,
                                repost_amt=repost_amt,
                                comment_amt=comment_amt,
                                published=timestamp
                            )
                        )
    for article in res:
        article.save()
    return res

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(download_vc_articles())
