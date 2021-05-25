import scrapy
from urllib.parse import urlencode
import json
from ..items import LocationItem
from datetime import datetime, date

API = ""
locations_ids = ["184317251608503"]


def get_proxyurl(url):
    payload = {"api_key": API, "proxy": "residential", "timeout": "20000", "url": url}
    proxy_url = "https://api.webscraping.ai/html?" + urlencode(payload)
    return proxy_url


class TagSpider(scrapy.Spider):
    name = "locationspider"
    allowed_domains = ["api.webscraping.ai"]
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
        "FEED_URI": "locationspider-" + str(date.today()) + ".json",
        "FEED_FORMAT": "json",
        "FEED_EXPORTERS": {
            "json": "scrapy.exporters.JsonItemExporter",
        },
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def start_requests(self):
        for location_id in locations_ids:
            url = f"https://www.instagram.com/explore/locations/{location_id}/?hl=en"
            yield scrapy.Request(get_proxyurl(url), callback=self.parse)

    def parse(self, response):
        item = LocationItem()
        xpath_query = response.xpath(
            "//script[starts-with(.,'window._sharedData')]/text()"
        ).get()
        response_string = "{" + xpath_query.strip().split("= {")[1][:-1]
        location_data = json.loads(response_string)

        location_id = location_data["entry_data"]["LocationsPage"][0]["graphql"][
            "location"
        ]["id"]
        has_next_page = location_data["entry_data"]["LocationsPage"][0]["graphql"][
            "location"
        ]["edge_location_to_media"]["page_info"]["has_next_page"]
        edges = location_data["entry_data"]["LocationsPage"][0]["graphql"]["location"][
            "edge_location_to_media"
        ]["edges"]

        for node in edges:
            item = LocationItem()
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
            cursor = location_data["entry_data"]["LocationsPage"][0]["graphql"][
                "location"
            ]["edge_location_to_media"]["page_info"]["end_cursor"]
            variables = {"id": location_id, "first": 12, "after": cursor}
            params = {
                "query_hash": "1b84447a4d8b6d6d0426fefb34514485",
                "variables": json.dumps(variables),
            }
            url = "https://www.instagram.com/graphql/query/?" + urlencode(params)
            request = scrapy.Request(get_proxyurl(url), callback=self.parse_pages)
            request.meta["variables"] = variables
            yield request
        else:
            yield item

    def parse_pages(self, response):
        item = LocationItem()
        variables = response.meta["variables"]
        location_data = json.loads(response.text)

        for node in location_data["data"]["location"]["edge_location_to_media"][
            "edges"
        ]:
            item = LocationItem()
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

        has_next_page = location_data["data"]["location"]["edge_location_to_media"][
            "page_info"
        ]["has_next_page"]
        if has_next_page:
            cursor = location_data["data"]["location"]["edge_location_to_media"][
                "page_info"
            ]["end_cursor"]
            variables["after"] = cursor
            params = {
                "query_hash": "1b84447a4d8b6d6d0426fefb34514485",
                "variables": json.dumps(variables),
            }
            url = "https://www.instagram.com/graphql/query/?" + urlencode(params)
            request = scrapy.Request(get_proxyurl(url), callback=self.parse_pages)
            request.meta["variables"] = variables
            request.meta["item"] = item
            yield request

    def get_video(self, response):
        item = response.meta["item"]
        video_url = response.xpath('//meta[@property="og:video"]/@content').get()
        item["video_url"] = video_url
        yield item
