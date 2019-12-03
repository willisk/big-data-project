from bs4 import BeautifulSoup
from torrequest import TorRequest
#from fake_useragent import UserAgent
from fake_headers import Headers
#from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxylessTask
import numpy as np
import requests, os, time, pickle
from pdfparser import parse_pdf

#search_base_url = 'https://scholar.google.com/scholar?hl=en&q={0}+filetype%3Apdf'

#terms = {'smart cities big data', 'data optimization intelligent city'}

random_keywords = { 'car ecological human design machine transport architecture' }

# %PDF-1.4
# <!DOCTYPE HTML>

### load/save pickle files

def pickle_load(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

def pickle_save(_dict, filename):
    with open(filename, 'wb') as f:
        pickle.dump(_dict, f, protocol=pickle.HIGHEST_PROTOCOL)



class Crawler:
    def __init__(self):

        self._save_results = False
        self._use_tor = False
        self._use_fake_headers = True

        self._term = 'smart city big data'
        #self._term = 'artificial intelligence cities future'
        #self.term = 'quantum tunnel'
        self._filetype = 'html'
        self._search_base_url = \
                'https://scholar.google.com/scholar?q={0}%20filetype:{3}&hl=en&start={2}&num={1}'
        
        self.crawl_pickle_file = 'data/results.pickle'
        self.query_pickle_file = 'data/query.pickle'
        self._download_folder = 'data/download/'



        #self.search_base_url = \
        #'https://scholar.google.com/scholar?hl=en&q={0}'

        self.tr = TorRequest(password = 'eaoCifoaaaoD:P')
        self.fake_header = Headers(headers = True)

        self.delays = [4, 8, 7, 2, 10, 16]
        self.requests_before_rotate = 5
        
        self.results_per_page = 20 # max
        self.search_pages_max = 50 # max results from google is 1000 = 50 * 20
        self.skip_pages = 0 # have crawler start at certain page number

        self.load_search_results()
        self.load_query_history()

    def run(self):

        print('current IP: {}'.format(requests.get('http://ipecho.net/plain').text))

        self.rotate_id()
        
        rotate_in = self.requests_before_rotate

        for i in range(self.search_pages_max):

            page = i + self.skip_pages
            query = self._term + ' filetype:' + self._filetype + ' page:' + str(page)

            ## check if query has been already used
            if query in self.query_history:
                print('already searched for "{}", continuing'.format(query))
                continue


            ## generate new id
            if( rotate_in + np.random.rand() * 2 <= 0 ):
                self.rotate_id()

            ## add random delay
            if not i == 0:
                delay = np.random.choice(self.delays) + np.random.rand()
                time.sleep(delay)


            #build url
            start_at = self.results_per_page * page
            self.request_url = self._search_base_url.format(self._term, self.results_per_page, start_at, self._filetype)

            ### send request
            try:
                if(self._use_tor):
                    if(self._use_fake_headers):
                        self.response = tr.get(self.request_url, headers = self.headers, stream = True)
                    else:
                        self.response = tr.get(self.request_url)
                else:
                    self.response = requests.get(self.request_url)
            except:
                print('SPOTTET, response took too long')
                break
            
            ### parse html response
            soup = BeautifulSoup(self.response.text, 'html.parser')
            query_headliners = soup.select('h3')

            if len(query_headliners) == 0:
                print('SPOTTET, no search results\n')
                self.write_server_response()
                break

            for h in query_headliners:
                if(h.a == None):
                    continue
                url = h.a.get('href')
                filename = url.split('/')[-1]
                name = filename.split('.' + self._filetype)[0] + '.' + self._filetype
                self.search_results[name] = url

            print('query "{0}" {1} unique results'.format(query, len(self.search_results)))

            if(self._save_results):
                self.query_history.add(query)    #add successful query to history

                self.save_search_results()
                self.save_query_history()



    ### parsing
    def parse_pdfs(self):
        if not os.path.exists('data/parsed/'):
            os.makedirs('data/parsed/')

        to_parse = []
        for entry in os.scandir('data/download/'):
            filename = os.fsdecode(entry)
            to_parse.append(filename)

        total = len(to_parse)

        for i, filename in enumerate(to_parse):
            filetype = filename.split('.')[-1]
            name = filename.split('/')[-1].split('.' + filetype)[0]
            filename_out = 'data/parsed/' + name + '-' + filetype + '.txt'
            if os.path.isfile(filename_out):
                print('skipping {}, file already parsed'.format(name))
            else:
                #start parsing
                if filetype == 'pdf':
                    print('parsing {}/{}: pdf {}'.format(i, total, name))
                    try:
                        parse_pdf(filename, filename_out)
                    except Exception as e:
                        print('caught Exception: ', e)
                        os.remove(filename_out)
                elif filetype == 'html':
                    print('parsing html ', name)
                




    ### fetch
    def fetch_data(self):
        if not os.path.exists(self._download_folder):
            os.makedirs(self._download_folder)
        
        count = 0
        failed = {}
        
        for key in self.search_results:
            filepath = self._download_folder + key
            if os.path.isfile(filepath):
                print('skipping {}, already downloaded'.format(key))
            else:
                print('downloading {}..'.format(key))
                url = self.search_results[key]
                try:
                    response = requests.get(url, stream = True)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    count += 1
                except Exception as e:
                    print('caught Exception: ', e)
                    failed[key] = e
        
        print('finished downloading {} files'.format(count))
        print('failed downloading:')
        for key in failed:
            print(key)
            print('-->', failed[key])



    ### load

    def load_search_results(self):
        if(not os.path.exists(self.crawl_pickle_file)):
            self.search_results = {}
        else:
            self.search_results = pickle_load(self.crawl_pickle_file)

    def load_query_history(self):
        if(not os.path.exists(self.query_pickle_file)):
            self.query_history = {''}
        else:
            self.query_history = pickle_load(self.query_pickle_file)
    

    ### save

    def save_search_results(self):
        pickle_save(self.search_results, self.crawl_pickle_file)

    def save_query_history(self):
        pickle_save(self.query_history, self.query_pickle_file)


    ### util

    def rotate_id(self):
        if(self._use_tor):
            print('Rotating id .. ')
            self.tr = TorRequest(password = 'eaoCifoaaaoD:P')
            self.tr.reset_identity()
            print('new IP: {}'.format(self.tr.get('http://ipecho.net/plain').text))
        if(self._use_fake_headers):
            self.headers = self.fake_header.generate()
            print('new User-Agent: {}\n'.format(self.headers['User-Agent']))

    def write_server_response(self):
        print('writing server_response.html ..')
        with open('server_response.html', 'w') as f:
            f.write(self.response.text)

    def dump_results(self):
        print('results dumped to /data/results_dump.txt ..')
        with open('data/results_dump.txt', 'w') as f:
            f.write(str(self.search_results))


import re
from shutil import copyfile

def pre_filter():
    should_contain = {'abstract': 2, 'abstract-': 2,
    'introduction': 2, 'conclusion': 1, 'conclusions': 1, 
    'acknowledgements': 1, 'references': 3, 'bibliography': 2}
    filtered = 'data/filtered'
    if not os.path.exists(filtered):
        os.makedirs(filtered)
    if not os.path.exists(filtered + '/questionable'):
        os.makedirs(filtered + '/questionable')
    for entry in os.scandir('data/parsed'):
        fname = os.fsdecode(entry)
        if os.path.isfile(fname):
            with open(fname, 'r', encoding='latin_1') as f:
                score = 0
                for line in f:
                    for word in should_contain:
                        if re.search(r'\b' + word + r'\b', line, re.IGNORECASE):
                            score += should_contain[word]
                if score >= 5:
                    copyfile(fname, filtered + '/' + fname.split('/')[-1])
                elif score == 4: 
                    copyfile(fname, filtered + '/questionable/' + fname.split('/')[-1])
                else:
                    print('filtered out {} with score {}'.format(fname, score))
                # if i == 30:
                #     break

import codecs
def concatenate():
    with codecs.open('data/concatenated.txt', 'wb') as c_file:
        for entry in os.scandir('data/filtered'):
            fname = os.fsdecode(entry)
            if os.path.isfile(fname):
                with codecs.open(fname, 'rb') as f:
                    line = f.read()
                    line = line.decode('latin1').encode('utf-8')
                    c_file.write(line)
                    c_file.write('\n<|endoftext|>\n'.encode('utf-8'))

#concatenate()

carl = Crawler()
#carl.parse_pdfs()
