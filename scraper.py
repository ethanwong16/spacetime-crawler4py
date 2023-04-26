import re
from collections import defaultdict
from urllib.parse import urlparse
from utils.response import Response
from bs4 import BeautifulSoup
import re
from collections import defaultdict


class ReportStatisticsLogger:
    def __init__(self):
        # set of non-ICS subdomain unique page URLs (de-fragmented)
        self._general_visited_pages = set()
        # ICS subdomain page URLs (de-fragmented), e.g. {subdomain : {URLs}}
        self._ics_visited_pages = defaultdict(set)
        # max encountered num words of page (longest page length)
        self._max_words: int = 0
        # non-stop word frequency counts, e.g. {word : frequency}
        self._word_frequencies = defaultdict(int)

        # parse stop words into global set
        self._init_stop_words()

    def _init_stop_words(self) -> None:
        # TODO : fix the stop words
        try:
            with open('stop.txt') as file:
                self.STOP_WORDS = set(line.rstrip().lower() for line in file)
        except Exception as error:
            print("YOU DUMB BRUH! THE ONLY THING STOPPED IS YOUR BRAIN")
            raise error

    def update_max_word_count(self, new_count: int) -> None:
        # print(new_count)
        if new_count > self._max_words:
            self._max_words = new_count

    def update_word_freqs(self, raw_tokens: list[str]) -> int:
        num_good_tokens = 0
        for good_token in filter(lambda token: token not in self.STOP_WORDS, map(str.lower, raw_tokens)):
            # print(good_token)
            self._word_frequencies[good_token] += 1
            num_good_tokens += 1
        return num_good_tokens
    
    def add_url(self, url):
        # checks if hostname has already been visited and increases number of unique pages if it hasn't (first bullet of second section of wiki)
        self._general_visited_pages.add(url)
        parsed = urlparse(url)
        if parsed.hostname in ['www.ics.uci.edu','www.cs.uci.edu/', 'www.informatics.uci.edu','www.stat.uci.edu'] and "#" not in url:
            self._ics_visited_pages[parsed.hostname].add(url)

    def get_stats(self):
        print(f'Total Pages : {self._general_visited_pages}')
        print(f'ICS Pages : {self._ics_visited_pages}')
        print(f'Word Count : {self._max_words}')
    # def write_statistics(self):
    #     word_tuples_list = sorted([(key, val) for key, val in self._word_frequencies.items()], key=lambda x: -x[1])
    #     final_word_tuples_list = []

    #     if len(word_tuples_list) < 50:
    #         final_word_tuples_list = [key for key, val in word_tuples_list]
    #     else:
    #         final_word_tuples_list = [word_tuples_list[i][0] for i in range(50)]

    #     with open('statistics.txt', "w") as f:
    #         global number_of_unique_pages
    #         f.write(str(len(visited_unique_hostnames)) + '\n')

    #         global longest_page_length
    #         f.write(str(longest_page_length) + '\n')

    #         f.write(str(final_word_tuples_list) + '\n')

    #         global subdomains_dict
    #         f.write(str(subdomains_dict) + '\n')


StatsLogger: ReportStatisticsLogger = ReportStatisticsLogger()


def scraper(url, resp: Response):
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!

    # TODO : check the status code
    if resp.status == 200:
        # TODO : parse webpage content & extract data
        soup = BeautifulSoup(resp.raw_response.content, "lxml")

        StatsLogger.add_url(resp.url)

        # refers to word frequencies (3rd bullet of section 3 of wiki)
        valid_words = 0
        for tag_content in soup.stripped_strings:
            # TODO : make time ranges work and solve bugs
            # printing out content
            raw_tokens = re.findall("[A-Za-z]+'s|[A-Za-z0-9]+@[A-Za-z.]+|[A-Za-z-A-Za-z]+|[A-Za-z-A-Za-z]+$|[A-Za-z0-9][A-Za-z0-9:.-@]+", tag_content)
            
            # TODO : utilize textual relevance score
            valid_words += StatsLogger.update_word_freqs(raw_tokens)
            # print(valid_words)
            # if valid_words < len(raw_tokens):
            #     pass
        StatsLogger.update_max_word_count(valid_words)

        # # updates longest page variable (2nd bullet of section 2 of wiki)
        # global longest_page_length
        # longest_page_length = max(num_words, longest_page_length)

        # # print(num_words)
        # # print(word_freqs)

        # StatsLogger.get_stats()
        # print()
        links = extract_next_links(url, resp)
        return [link for link in links if is_valid(link)]
    else:
        print(f'Error Code {resp.status}: {resp.error}')
        return []

def extract_next_links(url, resp):
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    # print(url)
    # print(resp.url)
    u = urlparse(url)
    domain = "https://" + u.netloc
    links = set()
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    for link in soup.find_all('a'):
        possible_url = link.get('href')
        # converts any relative url to become an absolute url
        if "html" not in link.get('href'): # checks if url missing scheme
            if "www" not in possible_url: # checks if is also url missing host:port
                possible_url = domain + possible_url
            else: 
                possible_url = "https:" + possible_url
        links.add(possible_url)
    for url in links:
        print(url)
    return list()

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    domains = [
        '.ics.uci.edu/',
        '.cs.uci.edu/',
        '.informatics.uci.edu/',
        'stat.uci.edu/'
    ]
    
    try:
        parsed = urlparse(url)

        valid_domain = False

        for domain in domains:
            if domain in url:
                valid_domain = True
                break

        if parsed.scheme not in set(["http", "https"]):
            return False
        return valid_domain and not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise