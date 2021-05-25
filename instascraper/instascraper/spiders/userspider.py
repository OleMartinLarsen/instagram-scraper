import scrapy
from urllib.parse import urlencode
import json
from ..items import UserItem
from datetime import datetime, date

API = ""
userids = ["felixogdumle"]


def get_proxyurl(url):
    payload = {"api_key": API, "proxy": "residential", "timeout": "20000", "url": url}
    proxy_url = "https://api.webscraping.ai/html?" + urlencode(payload)
    return proxy_url


class UserSpider(scrapy.Spider):
    name = "userspider"
    allowed_domains = ["api.webscraping.ai"]
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
        "FEED_URI": "userspider-" + str(date.today()) + ".json",
        "FEED_FORMAT": "json",
        "FEED_EXPORTERS": {
            "json": "scrapy.exporters.JsonItemExporter",
        },
        "FEED_EXPORT_ENCODING": "utf-8",
        "ITEM_PIPELINES": {
            "instascraper.pipelines.UserMongoPipeline": 300,
        },
    }

    def start_requests(self):
        for userid in userids:
            url = f"https://www.instagram.com/{userid}/?hl=en"
            yield scrapy.Request(get_proxyurl(url), callback=self.parse)

    def parse(self, response):
        item = UserItem()

        xpath_query = response.xpath(
            "//script[starts-with(.,'window._sharedData')]/text()"
        ).get()
        response_string = "{" + xpath_query.strip().split("= {")[1][:-1]
        user_data = json.loads(response_string)

        _id = user_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["id"]
        has_next_page = user_data["entry_data"]["ProfilePage"][0]["graphql"]["user"][
            "edge_owner_to_timeline_media"
        ]["page_info"]["has_next_page"]
        username = user_data["entry_data"]["ProfilePage"][0]["graphql"]["user"][
            "username"
        ]
        name = user_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["full_name"]
        edges = user_data["entry_data"]["ProfilePage"][0]["graphql"]["user"][
            "edge_owner_to_timeline_media"
        ]["edges"]

        posts = []

        for node in edges:
            post_data = {
                "post_url": "",
                "is_video": "",
                "image_url": "",
                "video_url": "",
                "post_date": "",
                "location": "",
                "like_count": "",
                "comment_count": "",
                "caption": "",
            }
            location = ""
            caption = ""

            post_url = "https://www.instagram.com/p/" + node["node"]["shortcode"]
            is_video = node["node"]["is_video"]
            if is_video:
                image_url = node["node"]["display_url"]
                video_url = node["node"]["video_url"]
            else:
                image_url = node["node"]["thumbnail_resources"][-1]["src"]
                video_url = ""
            post_date = datetime.fromtimestamp(
                node["node"]["taken_at_timestamp"]
            ).strftime("%d/%m/%Y %H:%M:%S")
            if node["node"]["location"] is not None:
                location = node["node"]["location"]["slug"]
            like_count = node["node"]["edge_media_preview_like"]["count"]
            comment_count = node["node"]["edge_media_to_comment"]["count"]
            if node["node"]["edge_media_to_caption"]:
                edges = node["node"]["edge_media_to_caption"]["edges"]
                for node in edges:
                    caption = node["node"]["text"]

            post_data["post_url"] = post_url
            post_data["is_video"] = is_video
            post_data["video_url"] = video_url
            post_data["image_url"] = image_url
            post_data["post_date"] = post_date
            post_data["location"] = location
            post_data["like_count"] = like_count
            post_data["comment_count"] = comment_count
            post_data["caption"] = caption

            posts.append(post_data)

        item["_id"] = _id
        item["username"] = username
        item["name"] = name
        item["posts"] = posts

        if has_next_page:
            cursor = user_data["entry_data"]["ProfilePage"][0]["graphql"]["user"][
                "edge_owner_to_timeline_media"
            ]["page_info"]["end_cursor"]
            variables = {"id": _id, "first": 12, "after": cursor}
            params = {
                "query_hash": "02e14f6a7812a876f7d133c9555b1151",
                "variables": json.dumps(variables),
            }
            url = "https://www.instagram.com/graphql/query/?" + urlencode(params)
            request = scrapy.Request(get_proxyurl(url), callback=self.parse_pages)
            request.meta["pages_variables"] = variables
            request.meta["item"] = item
            yield request
        else:
            yield item

    def parse_pages(self, response):
        item = response.meta["item"]
        variables = response.meta["pages_variables"]
        user_data = json.loads(response.text)
        posts = item["posts"]

        for node in user_data["data"]["user"]["edge_owner_to_timeline_media"]["edges"]:
            post_data = {
                "post_url": "",
                "is_video": "",
                "image_url": "",
                "video_url": "",
                "post_date": "",
                "location": "",
                "like_count": "",
                "comment_count": "",
                "caption": "",
            }
            location = ""
            caption = ""

            post_url = "https://www.instagram.com/p/" + node["node"]["shortcode"]
            is_video = node["node"]["is_video"]
            if is_video:
                image_url = node["node"]["display_url"]
                video_url = node["node"]["video_url"]
            else:
                image_url = node["node"]["thumbnail_resources"][-1]["src"]
                video_url = ""
            image_url = node["node"]["thumbnail_resources"][-1]["src"]
            post_date = datetime.fromtimestamp(
                node["node"]["taken_at_timestamp"]
            ).strftime("%d/%m/%Y %H:%M:%S")
            if node["node"]["location"] is not None:
                location = node["node"]["location"]["slug"]
            like_count = node["node"]["edge_media_preview_like"]["count"]
            comment_count = node["node"]["edge_media_to_comment"]["count"]
            if node["node"]["edge_media_to_caption"]:
                edges = node["node"]["edge_media_to_caption"]["edges"]
                for node in edges:
                    caption = node["node"]["text"]

            post_data["post_url"] = post_url
            post_data["is_video"] = is_video
            post_data["video_url"] = video_url
            post_data["image_url"] = image_url
            post_data["post_date"] = post_date
            post_data["location"] = location
            post_data["like_count"] = like_count
            post_data["comment_count"] = comment_count
            post_data["caption"] = caption

            posts.append(post_data)

        item["posts"] = posts

        next_page_bool = user_data["data"]["user"]["edge_owner_to_timeline_media"][
            "page_info"
        ]["has_next_page"]
        if next_page_bool:
            cursor = user_data["data"]["user"]["edge_owner_to_timeline_media"][
                "page_info"
            ]["end_cursor"]
            variables["after"] = cursor
            params = {
                "query_hash": "02e14f6a7812a876f7d133c9555b1151",
                "variables": json.dumps(variables),
            }
            url = "https://www.instagram.com/graphql/query/?" + urlencode(params)
            request = scrapy.Request(get_proxyurl(url), callback=self.parse_pages)
            request.meta["pages_variables"] = variables
            request.meta["item"] = item
            yield request
        else:
            yield item
