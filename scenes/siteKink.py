import re

import scrapy

from tpdb.BaseSceneScraper import BaseSceneScraper


class KinkFeaturedSpider(BaseSceneScraper):
    name = 'Kink'
    network = "Kink"

    url = 'https://www.kink.com'

    paginations = [
        '/shoots/latest?page=%s',
        '/shoots/featured?page=%s',
        '/shoots/partner?page=%s',
    ]

    selector_map = {
        'title': '//title/text()',
        'description': '//span[@class="description-text"]/p/text()',
        'date': "//span[@class='shoot-date']/text()",
        'image': '//meta[@name="twitter:image"]/@content',
        'performers': '//p[@class="starring"]/span/a/text()',
        'tags': "//a[@class='tag']/text()",
        'external_id': '\\/shoot\\/(\\d+)',
        'trailer': '//meta[@name="twitter:player"]/@content',
        'pagination': '/shoots/latest?page=%s'
    }

    def start_requests(self):
        for pagination in self.paginations:
            yield scrapy.Request(url=self.get_next_page_url(self.url, self.page, pagination),
                                 callback=self.parse,
                                 meta={
                'page': self.page, 'pagination': pagination},
                headers=self.headers,
                cookies=self.cookies)

    def parse(self, response, **kwargs):
        if response.status == 200:
            scenes = self.get_scenes(response)
            count = 0
            for scene in scenes:
                count += 1
                yield scene

            if count:
                if 'page' in response.meta and response.meta['page'] < self.limit_pages:
                    meta = response.meta
                    meta['page'] = meta['page'] + 1
                    print('NEXT PAGE: ' + str(meta['page']))
                    yield scrapy.Request(url=self.get_next_page_url(self.url, meta['page'], meta['pagination']),
                                         callback=self.parse,
                                         meta=meta,
                                         headers=self.headers,
                                         cookies=self.cookies)

    def get_scenes(self, response):
        scenes = response.xpath("//a[@class='shoot-link']/@href").getall()
        for scene in scenes:
            if re.search(self.get_selector_map('external_id'), scene):
                yield scrapy.Request(url=self.format_link(response, scene), callback=self.parse_scene)

    def get_site(self, response):
        return response.xpath(
            '//div[@class="shoot-page"]/@data-sitename').get().strip()

    def get_performers(self, response):
        performers = self.process_xpath(
            response, self.get_selector_map('performers')).getall()
        performers_stripped = [s.strip() for s in performers]
        performers_stripped = [s.rstrip(',') for s in performers_stripped]
        return list(map(lambda x: x.strip(), performers_stripped))

    def get_next_page_url(self, url, page, pagination):
        return self.format_url(url, pagination % page)
