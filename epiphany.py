import asyncio
import bs4
import tldextract
import aiohttp
from time import time
from urllib.request import urljoin
from urllib.parse import urlparse
from contextlib import suppress
import argparse
import os
import random
from page import Page
from file_manager import File_Manager


class Crawler(File_Manager):
    CONDITIONS = {
        "part_of_link": (lambda self, link: urljoin(self.host, link) if link.startswith('/') else link),
        "is_not_visited": (lambda self, link: True if link not in self.visited_urls else False),
        "not_in_ext": (lambda self, link: False if link.endswith(self.unnecessary_extensions) else True),
        "is_current_host": (lambda self, link: False if tldextract.extract(link).domain != tldextract.extract(
            self.host).domain else True),
        "is_url": (lambda self, link: True if link.startswith(self.schemes) else False)
    }

    unnecessary_extensions = ('.jpg', '.png', '.gif', '.pdf', '.jpg')
    schemes = ('https', 'http')
    payloads = ()

    def __init__(self, target_host, payload_path):

        self.visited_urls = set()
        self.host = target_host
        if urlparse(self.host).scheme not in self.schemes:
            self.host = 'https://' + self.host
        super(Crawler, self).__init__(f'reports/{tldextract.extract(self.host).domain}.csv', payload_path)
        self.timeout = aiohttp.ClientTimeout(total=None, sock_connect=40, sock_read=40)

    async def request(self, page, req_sema, client):

        """
        Send request to URL and get page load time

        Parameters
        --------------

            page : Page,
                Page Object
            req_sema : asyncio.Semaphore
                Semaphore 
            client : aiohttp.ClientSession
                ClientSession 

        Returns
        ------------
        list( page_content, current_url )

        """

        print(f'{page.method} - {page.url}')
        data = None
        async with req_sema:
            start_time = time()
            try:
                req = getattr(client, page.method)
                async with req(page.url, data=page.payload, allow_redirects=False, timeout=self.timeout) as resp:
                    data = await resp.content.read()
                    end_time = time()
                    page.first_load_time = end_time - start_time
                start_time = time()
                async with req(page.url, data=page.payload, allow_redirects=False, timeout=self.timeout) as resp:
                    data = await resp.content.read()
                    end_time = time()
                    page.second_load_time = end_time - start_time
                    page.cache_control = resp.headers.get('Cache-Control')
                    page.expires = resp.headers.get('Expires')
                    page.etag = resp.headers.get('ETag')
                    page.last_modified = resp.headers.get('Last-Modified')
            except Exception as ex:
                print(ex)
            finally:
                await self.write_to_file(
                    row=[page.method, page.url, page.first_load_time, page.second_load_time, page.cache_control,
                         page.expires, page.etag, page.last_modified])
                return [data, page.url]

    async def parse(self, data, req_sema, client):

        """
        Page parse, get all <a> and <form> tags

        Parameters
        --------------

            data : list,
                Page content and parent url
            req_sema : asyncio.Semaphore
                Semaphore 
            client : aiohttp.ClientSession
                ClientSession 

        """

        if data[0]:
            pages = []
            soup = bs4.BeautifulSoup(data[0], 'html.parser', from_encoding="iso-8859-1")
            links_list = soup.find('body')
            if links_list:
                links_list_items = links_list.find_all('a')
                forms = links_list.find_all('form')
                pages.extend([path for link in links_list_items if (path := self.__validate_link__(link))])
                pages.extend([path for form in forms if (path := self.__validate_link__(form, data[1]))])
            await self.crawl(pages, req_sema, client)

    def __validate_link__(self, obj, parent=None):

        """
        Check link

        Parameters
        --------------

            obj : bs4 tag,
                Beautiful Soup Tag
            parent : str (optional)
                Parent url 

        """

        page = Page()
        if obj.name == 'form':
            page.url = obj.get('action') if obj.get('action') else parent
            page.method = obj.get('method').lower() if obj.get('method') else 'post'
            page.payload = {i.get('name'): random.sample(self.payloads, 1) for i in obj.find_all(lambda tag:
                                                                                                 tag.name == "input" and
                                                                                                 tag.attrs.get(
                                                                                                     'type') not in (
                                                                                                     'submit',
                                                                                                     'hidden'))}
        else:
            page.url = urlparse(obj.get('href'))._replace(query=None).geturl()
        if page.url:
            page.url = self.CONDITIONS['part_of_link'](self, page.url)
            if self.CONDITIONS['is_not_visited'](self, (page.url, page.method)) and self.CONDITIONS['is_current_host'](
                    self, page.url) and self.CONDITIONS['not_in_ext'](self, page.url) and self.CONDITIONS['is_url'](
                    self, page.url):
                self.visited_urls.add((page.url, page.method))
                return page

    async def crawl(self, pages, req_sema, client):

        """
        Collection of information

        Parameters
        --------------

            pages : list,
                list of pages
            req_sema : asyncio.Semaphore
                Semaphore 
            client : aiohttp.ClientSession
                ClientSession 

        """

        for request_future in asyncio.as_completed([self.request(page, req_sema, client) for page in pages]):
            data = await request_future
            await self.parse(data, req_sema, client)

    async def main(self):

        """
        Starting point for crawling
        """

        req_sema = asyncio.Semaphore(value=50)
        await self.write_to_file('w', row=self.table_header)
        self.payloads = await self.read_from_file(self.path_to_payloads)
        async with aiohttp.ClientSession(raise_for_status=True, trust_env=True) as client:
            await self.crawl([Page(self.host, 'get')], req_sema, client)


if __name__ == '__main__':

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    try:
        # Get args
        parser = argparse.ArgumentParser(prog='epiphany',
                                         usage='%(prog)s [options] hosts separated by spaces [payload]')
        parser.add_argument('hosts', nargs='*', help='Destination Hosts')
        parser.add_argument('payload',
                            help='Path to the file with payload data for the POST requests',
                            default='payloads')
        parser.add_argument('-oC', action='store_true', help='Output result to console')
        args = parser.parse_args()

        for host in args.hosts:

            if os.path.isfile(args.payload):
                crw = Crawler(host, args.payload)
                # Run
                loop.run_until_complete(crw.main())
                loop.run_until_complete(crw.sort_file())
                if args.oC:
                    loop.run_until_complete(crw.show_in_terminal())

    except KeyboardInterrupt:
        for task in asyncio.all_tasks():
            task.cancel()
            with suppress(asyncio.CancelledError):
                loop.run_until_complete(task)
    finally:
        loop.close()
