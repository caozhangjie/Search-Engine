# -*- coding: utf-8 -*-
import scrapy
import urllib2
import urllib
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
import threading


class GoogleSpider(scrapy.Spider):
    name = "multi-source_spider"
    default_meta = {"dont_obey_robotstxt": True, "dont_filter":True}
    default_headers=  {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
    counter = 0
    corpus_file = None
    corpus_text_file = None
    title_file = None
    tokenizer = RegexpTokenizer(r'\w+')
    lock_counter = threading.Lock()
    doc_counter = 0
    
    def errbacks(self, failure):
        try:
            print response.status
        except Exception as resaon:
            print resaon
    
    def start_requests(self):
        self.corpus_file = open("../../../data/corpus.txt", "w")
        self.corpus_text_file = open("../../../data/corpus_text.txt", "w")
        self.title_file = open("../../../data/titles.txt", "w")
        start_wds = ["game","sport","play","education", "commercial", "politic", "news"]
        meta = self.default_meta
        urls = []
        for t in start_wds:
            data = urllib.urlencode({"wd":t})
            urls.append('https://en.wikipedia.org/wiki/'+data)
            urls.append('http://global.bing.com/search?q='+data+'&setmkt=en-us')
        for url in urls:
            yield scrapy.Request(url=url, meta = meta, headers=self.default_headers, callback=self.parse, errback=self.errbacks)

    def parse(self, response):
        soup = BeautifulSoup(response.body, "html.parser")
        try:
            this_title = soup.find("head").findChild("title").contents[0].strip()
            file_ = open("../../../data/"+this_title+".html", "wb")
        except Exception as reason:
            file_ = open("../../../data/default_counter_"+str(self.counter)+".html", "wb")
            this_title = "default title " + str(self.counter)
            self.counter += 1
        file_.write(response.body)
        file_.close()
        try:
            next_pages = soup.find("body").findChildren("a")
            page_content = soup.find("body").text
        except Exception as reason:
            return
        write_content = self.preprocessing(response.url, this_title, page_content)
        self.corpus_file.write(write_content[0])
        self.corpus_file.flush()
        self.title_file.write(write_content[1])
        self.title_file.flush()
        self.corpus_text_file.write(write_content[2])
        self.corpus_text_file.flush()
        for raw_url in next_pages:
            try:
                raw_url = raw_url.attrs["href"]
                if raw_url != "/" or raw_url[0:10] != "javascript":
                    true_url = response.urljoin(raw_url)
                    yield scrapy.Request(url=true_url, meta = self.default_meta, headers=self.default_headers, callback=self.parse, errback=self.errbacks)
            except Exception as reason:
                print reason

    def preprocessing(self, url_add, raw_title, content):
        word_list = self.tokenizer.tokenize(content)
        title_list = self.tokenizer.tokenize(raw_title)
        return_str = ""
        title = ""
        for val in word_list:
            return_str += val + " "
        for val in title_list:
            title += val + " "
        while not self.lock_counter.acquire(1):
            continue
        return_list = []
        return_list.append(str(self.doc_counter) + "###" + url_add + "###" + title + " " + return_str + "\n")
        return_list.append(str(self.doc_counter) + "###" + title + "\n")
        return_list.append(str(self.doc_counter) + "###" + url_add + "###" + " " + return_str + "\n")
        self.doc_counter += 1
        self.lock_counter.release()
        return return_list
