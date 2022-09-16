import mongoengine
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from fake_useragent import UserAgent
import json
from ..models.WB import ProductWB, CommentWB
from rss_parser import Parser


async def download_wildberries_comments(query: str):
    """
    Function that downloads comments and products from https://www.wildberries.ru by user query (e.g. Whiskas)
    :param query: Query to search
    :return: List of products which were found by this query
    """
    # Открытие сессии
    async with aiohttp.ClientSession() as session:
        products = []
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user_agent": UserAgent()['google chrome']
        }

        url = (
            'https://search.wb.ru/exactmatch/ru/common/v3/search?appType=1&couponsGeo=12,3,18,15,21&curr=rub&dest=-1029256,-102269,-1278703,-1255563&emp=0&lang=ru&locale=ru&pricemarginCoeff=1.0&query='
            + str(query) +
            '&reg=0&regions=68,64,83,4,38,80,33,70,82,86,75,30,69,22,66,31,48,1,40,71&resultset=catalog&sort=popular&spp=0&stores=117673,122258,122259,125238,125239,125240,6159,507,3158,117501,120602,120762,6158,121709,124731,159402,2737,130744,117986,1733,686,132043'
        )
        # GET запрос к серверу для получения списка карточек
        async with session.get(url=url, headers=headers) as response_product:
            response_text_product = await response_product.text()
            json_obj_product = json.loads(response_text_product)
            if json_obj_product:
                for product in json_obj_product.get("catalog").get("data").get("products"):
                    url_imt = "https://wbx-content-v2.wbstatic.net/ru/" + str(product["id"]) + ".json"
                    async with session.get(url=url_imt, headers=headers) as response_imt:
                        response_text_imt = await response_imt.text()
                        json_obj_imt = json.loads(response_text_imt)
                    url_seller = (
                            "https://wbx-content-v2.wbstatic.net/sellers/" +
                            str(product["id"]) +
                            ".json"
                    )
                    async with session.get(url=url_seller, headers=headers) as response_seller:
                        response_text_seller = await response_seller.text()
                        if response_text_seller:
                            json_obj_seller = json.loads(response_text_seller)
                            seller_name = json_obj_seller.get("supplierName")
                        else:
                            seller_name = ''
                    if int(product["feedbacks"]) == 0:
                        continue
                    url = "https://public-feedbacks.wildberries.ru/api/v1/summary/full"
                    # Checking whether there is such product in DB or not
                    try:

                        found = ProductWB.objects(id_product=str(product["id"])).get()
                        print('IT WAS FOUND')
                    except mongoengine.DoesNotExist:
                        found = None
                    if found:
                        comments_amt_before = found.feedbacks_amt
                        comments_amt_after = int(product["feedbacks"])
                        index_to_download = range(int(int(comments_amt_after - comments_amt_before) / 30) + 1)
                    else:
                        comments_amt_before = 0
                        index_to_download = range(int(int(product["feedbacks"]) / 30) + 1)
                    for num_iter in index_to_download:
                        payload = {"imtId": int(json_obj_imt.get("imt_id")), "skip": 30 * num_iter + comments_amt_before,
                                   "take": 30}
                        async with session.post(
                                url=url, headers=headers, json=payload
                        ) as response:
                            response_text = await response.text()
                            if response_text:
                                json_obj = json.loads(response_text)
                                comments = []
                                for comment in json_obj.get("feedbacks"):
                                    if comment.get("votes"):
                                        pluses_amt = comment.get(
                                            "votes").get(
                                            "pluses"
                                        )
                                        minuses_amt = comment.get(
                                            "votes").get(
                                            "minuses"
                                        )
                                    else:
                                        pluses_amt = 0
                                        minuses_amt = 0

                                    comments.append(
                                        CommentWB(
                                            date=str(comment.get("createdDate")),
                                            author=str(comment.get(
                                                "wbUserDetails").get(
                                                "name"
                                            )),
                                            rating=comment.get('productValuation'),
                                            advantages=str(comment.get("pros")),
                                            disadvantages=str(comment.get("cons")),
                                            comment=str(comment.get("text")),
                                            pluses_amt=int(pluses_amt),
                                            minuses_amt=int(minuses_amt)
                                        )
                                    )

                    if found:
                        for comment in comments:
                            found.comments.append(comment)
                        found.feedbacks_amt = int(product["feedbacks"])
                        products.append(found)
                    else:
                        products.append(
                            ProductWB(
                                id_product=str(product["id"]),
                                imt_id=str(json_obj_imt.get("imt_id")),
                                name=str(json_obj_imt.get("imt_name")),
                                description=str(json_obj_imt.get("description")),
                                seller=seller_name,
                                category_name=str(product["name"]),
                                brand=str(product["brand"]),
                                price=int(product["salePriceU"]) / 100,
                                price_old=int(product["priceU"]) / 100,
                                url=(
                                    "https://www.wildberries.ru/catalog/"
                                    + str(product["id"])
                                    + "/detail.aspx?targetUrl=XS"
                                ),
                                rating=float(product["rating"]),
                                feedbacks_amt=int(product["feedbacks"]),
                                query=query,
                                comments=comments
                            )
                        )

        await asyncio.sleep(0.5)
    for product in products:
        product.save()
    return products


