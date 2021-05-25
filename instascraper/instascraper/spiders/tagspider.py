import scrapy
from urllib.parse import urlencode
import json
from ..items import TagItem
from datetime import datetime, date

API = ""
tags = ["hundkonnerud"]


def get_proxyurl(url):
    payload = {"api_key": API, "proxy": "residential", "timeout": "20000", "url": url}
    proxy_url = "https://api.webscraping.ai/html?" + urlencode(payload)
    return proxy_url


class TagSpider(scrapy.Spider):
    name = "tagspider"
    allowed_domains = ["api.webscraping.ai"]
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
        "FEED_URI": "tagspider-" + str(date.today()) + ".json",
        "FEED_FORMAT": "json",
        "FEED_EXPORTERS": {
            "json": "scrapy.exporters.JsonItemExporter",
        },
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def start_requests(self):
        for tag in tags:
            url = f"https://www.instagram.com/explore/tags/{tag}/?hl=en"
            yield scrapy.Request(get_proxyurl(url), callback=self.parse)

    def parse(self, response):
        xpath_query = response.xpath(
            "//script[starts-with(.,'window._sharedData')]/text()"
        ).get()
        response_string = "{" + xpath_query.strip().split("= {")[1][:-1]
        hashtag_data = json.loads(response_string)
        hashtag_name = hashtag_data["entry_data"]["TagPage"][0]["graphql"]["hashtag"][
            "name"
        ]
        has_next_page = hashtag_data["entry_data"]["TagPage"][0]["graphql"]["hashtag"][
            "edge_hashtag_to_media"
        ]["page_info"]["has_next_page"]
        edges = hashtag_data["entry_data"]["TagPage"][0]["graphql"]["hashtag"][
            "edge_hashtag_to_media"
        ]["edges"]

        for node in edges:
            item = TagItem()
            post_url = "https://www.instagram.com/p/" + node["node"]["shortcode"]
            caption = ""
            is_video = node["node"]["is_video"]

            if is_video:
                image_url = node["node"]["display_url"]
            else:
                image_url = node["node"]["thumbnail_resources"][-1]["src"]
            post_date = datetime.fromtimestamp(
                node["node"]["taken_at_timestamp"]
            ).strftime("%d/%m/%Y %H:%M:%S")
            like_count = node["node"]["edge_media_preview_like"]["count"]
            comment_count = node["node"]["edge_media_to_comment"]["count"]
            if node["node"]["edge_media_to_caption"]:
                edges = node["node"]["edge_media_to_caption"]["edges"]
                for node in edges:
                    caption = node["node"]["text"]

            item["post_url"] = post_url
            item["is_video"] = is_video
            item["image_url"] = image_url
            item["post_date"] = post_date
            item["like_count"] = like_count
            item["comment_count"] = comment_count
            item["caption"] = caption

            if is_video:
                video_request = scrapy.Request(
                    get_proxyurl(post_url), callback=self.get_video
                )
                video_request.meta["item"] = item
                yield video_request
            else:
                item["video_url"] = ""
                yield item

        if has_next_page:
            cursor = hashtag_data["entry_data"]["TagPage"][0]["graphql"]["hashtag"][
                "edge_hashtag_to_media"
            ]["page_info"]["end_cursor"]
            variables = {"tag_name": hashtag_name, "first": 12, "after": cursor}
            params = {
                "query_hash": "9b498c08113f1e09617a1703c22b2f32",
                "variables": json.dumps(variables),
            }
            url = "https://www.instagram.com/graphql/query/?" + urlencode(params)
            request = scrapy.Request(get_proxyurl(url), callback=self.parse_pages)
            request.meta["pages_variables"] = variables
            yield request

    def parse_pages(self, response):
        variables = response.meta["pages_variables"]
        hashtag_data = json.loads(response.text)

        for node in hashtag_data["data"]["hashtag"]["edge_hashtag_to_media"]["edges"]:
            item = TagItem()
            caption = ""
            post_url = "https://www.instagram.com/p/" + node["node"]["shortcode"]
            is_video = node["node"]["is_video"]
            image_url = node["node"]["thumbnail_resources"][-1]["src"]
            post_date = datetime.fromtimestamp(
                node["node"]["taken_at_timestamp"]
            ).strftime("%d/%m/%Y %H:%M:%S")
            like_count = node["node"]["edge_media_preview_like"]["count"]
            comment_count = node["node"]["edge_media_to_comment"]["count"]
            if node["node"]["edge_media_to_caption"]:
                edges = node["node"]["edge_media_to_caption"]["edges"]
                for node in edges:
                    caption = node["node"]["text"]

            item["post_url"] = post_url
            item["is_video"] = is_video
            item["image_url"] = image_url
            item["post_date"] = post_date
            item["like_count"] = like_count
            item["comment_count"] = comment_count
            item["caption"] = caption

            if is_video:
                video_request = scrapy.Request(
                    get_proxyurl(post_url), callback=self.get_video
                )
                video_request.meta["item"] = item
                yield video_request
            else:
                item["video_url"] = ""
                yield item

        has_next_page = hashtag_data["data"]["hashtag"]["edge_hashtag_to_media"][
            "page_info"
        ]["has_next_page"]
        if has_next_page:
            cursor = hashtag_data["data"]["hashtag"]["edge_hashtag_to_media"][
                "page_info"
            ]["end_cursor"]
            variables["after"] = cursor
            params = {
                "query_hash": "9b498c08113f1e09617a1703c22b2f32",
                "variables": json.dumps(variables),
            }
            url = "https://www.instagram.com/graphql/query/?" + urlencode(params)
            request = scrapy.Request(get_proxyurl(url), callback=self.parse_pages)
            request.meta["pages_variables"] = variables
            request.meta["item"] = item
            yield request

    def get_video(self, response):
        item = response.meta["item"]
        video_url = response.xpath('//meta[@property="og:video"]/@content').get()
        item["video_url"] = video_url
        yield item
