#

# STatus
# by company CSV:
# 0-50: part done
# 50-1000: part-done
# 1000+: not started

import re
import logging
import requests
from normality import slugify
from StringIO import StringIO
from unicodecsv import DictReader
from urlparse import urljoin
from datetime import datetime
from lxml import html

from aleph.crawlers import Crawler, TagExists


log = logging.getLogger(__name__)

DOMAIN = "http://www.asx.com.au/asx/"
CSV_URL = urljoin(DOMAIN, "research/ASXListedCompanies.csv")
ASX_URL = urljoin(DOMAIN, "research/companyInfo.do?by=asxCode&asxCode=%s")
API_URL = "http://data.asx.com.au/data/1/company/%s?fields=primary_share,latest_annual_reports,last_dividend,primary_share.indices"
ANN_URL = urljoin(DOMAIN, "statistics/announcements.do?by=asxCode&"
                          "asxCode=%s&timeframe=Y&year=%s")


def collapse_whitespace(text):
    """ Collapse all consecutive whitespace, newlines and tabs
    in a string into single whitespaces, and strip the outer
    whitespace. This will also accept an ``lxml`` element and
    extract all text. """
    if text is None:
        return None
    if hasattr(text, 'xpath'):
        text = text.xpath('string()')
    text = re.sub('\s+', ' ', text)
    return text.strip()


class ASXCrawler(Crawler):

    LABEL = "Australian Stock Exchange"
    SITE = "http://www.asx.com.au"
    MAX_COMPANIES = 10000
    COMPANY_OFFSET = 10020

    COMPANIES_SCRAPED = 0

    def store_announcement(self, data):
        try:
            res = requests.get(data['announcement_link'])
            doc = html.fromstring(res.content)
            url = doc.find('.//input[@name="pdfURL"]').get('value')
            url = urljoin(DOMAIN, url)
            self.check_tag(url=url)

            title = '%s (%s): %s' % (data.get('name_abbrev'),
                                     data.get('announcement_date'),
                                     data.get('announcement_headline'))
            log.info("%s / %s" % (data.get('code'), title))
            self.emit_url(url, title=title, meta=data)
            logging.info('ading url to queue: %s' % url)
        except TagExists:
            logging.info('skipping because tag exists -- %s' % url)
            pass

    def scrape_announcements(self, data):
        year_now = datetime.utcnow().year
        for year in range(year_now-10, year_now+1):
            ann_data = data.copy()
            url = ANN_URL % (data.get('code'), year)
            res = requests.get(url)
            doc = html.fromstring(res.content)
            xpath = './/table[@class="contenttable"]//tr'
            for row in doc.findall(xpath):
                tds = row.findall('.//td')
                if not len(tds):
                    continue
                date = collapse_whitespace(tds[0].text)
                date = datetime.strptime(date, '%d/%m/%Y')
                date = date.strftime('%Y-%m-%d')
                ann_data['announcement_date'] = date
                ann_data['announcement_year'] = year
                headline = collapse_whitespace(tds[2].text)
                ann_data['announcement_headline'] = headline
                link = tds[4].find('.//a').get('href')
                link = urljoin(DOMAIN, link)
                ann_data['announcement_link'] = link
                self.store_announcement(ann_data)

    def scrape_company(self, data):
        if self.COMPANIES_SCRAPED < self.COMPANY_OFFSET:
            self.COMPANIES_SCRAPED += 1
            logging.debug('skipping %s' % data.get('code', 'unknown'))
            return
        if self.COMPANIES_SCRAPED > self.MAX_COMPANIES + self.COMPANY_OFFSET:
            logging.info('finished companies at no. %s' % self.COMPANIES_SCRAPED)
            return
        self.COMPANIES_SCRAPED += 1
        logging.info('scraping %s' % data)
        url = API_URL % data.get('ASX code')
        data.update(requests.get(url).json())
        if 'code' not in data:
            return
        data['Stock Info URL'] = url
        data.pop('ASX code', None)
        data.pop('primary_share', None)
        data.pop('last_dividend', None)
        data.pop('latest_annual_reports', None)
        data.pop('products', None)

        record = {}
        for k, v in data.items():
            record[slugify(k, sep='_')] = v

        category = slugify(record['gics_industry_group'])
        if category not in ['materials', 'energy']:
            logging.info('skipping category %s' % category)
            return

        self.scrape_announcements(data)

    def crawl(self):
        logging.warn('starting asx crawl')
        res = requests.get(CSV_URL)
        header, body = res.content.split('\r\n\r\n', 1)
        sio = StringIO(body)
        logging.warn('about to start processing asx')
        for row in list(DictReader(sio)):
            row['source_info'] = header.strip()
            try:
                self.scrape_company(row)
            except Exception, e:
                log.exception(e)
