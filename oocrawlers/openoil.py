import logging
import requests
from lxml import etree
from urlparse import urljoin

from aleph.crawlers import Crawler, TagExists

log = logging.getLogger(__name__)

NS = '{http://s3.amazonaws.com/doc/2006-03-01/}'
BUCKET = 'https://s3-eu-west-1.amazonaws.com/downloads.openoil.net/?prefix=contracts/'


class OpenOilCrawler(Crawler):

    LABEL = "OpenOil"
    SITE = "http://repository.openoil.net/"

    def crawl(self):
        res = requests.get(BUCKET)
        doc = etree.fromstring(res.content)
        for key in doc.findall('.//%sKey' % NS):
            if not key.text.endswith('.pdf'):
                continue
            url = urljoin(BUCKET, key.text)
            try:
                self.check_tag(url=url)
                self.emit_url(url)
            except TagExists:
                pass
