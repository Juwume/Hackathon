#import mongoengine
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from fake_useragent import UserAgent
import json
from rss_parser import Parser
from xml.etree import ElementTree as ET


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
    async with aiohttp.ClientSession() as session:
        products = []
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user_agent": UserAgent()['google chrome']
        }
        url = 'https://vc.ru/rss'
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
                    paragraphs = soup.find("div", class_='content content--full').find_all("div",
                                                                              class_="l-island-a")
                    hash_tags = paragraphs[-2].get_text().strip()
                    print(hash_tags)
                    if '#' not in hash_tags:
                        hash_tags = ''
                    print(hash_tags.replace('#', '').split())


                    # for item in paragraphs:
                    #     print('-----------')
                    #     print(item.get_text())

                    print(soup.title.string)


    return None

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(download_vc_articles())
