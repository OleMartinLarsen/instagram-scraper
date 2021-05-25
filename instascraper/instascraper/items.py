# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UserItem(scrapy.Item):
    _id = scrapy.Field()
    username = scrapy.Field()
    name = scrapy.Field()
    posts = scrapy.Field()


class TagItem(scrapy.Item):
    post_url = scrapy.Field()
    is_video = scrapy.Field()
    image_url = scrapy.Field()
    video_url = scrapy.Field()
    post_date = scrapy.Field()
    like_count = scrapy.Field()
    comment_count = scrapy.Field()
    caption = scrapy.Field()


class LocationItem(scrapy.Item):
    post_url = scrapy.Field()
    is_video = scrapy.Field()
    image_url = scrapy.Field()
    video_url = scrapy.Field()
    post_date = scrapy.Field()
    like_count = scrapy.Field()
    comment_count = scrapy.Field()
    caption = scrapy.Field()
