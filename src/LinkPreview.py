from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import requests

# Headers used by BeautifulSoup to search for website data.
headers = {'Access-Control-Allow-Origin': '*',
           'Access-Control-Allow-Methods': 'GET',
           'Access-Control-Allow-Headers': 'Content-Type',
           'Access-Control-Max-Age': '3600',
           'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'}

# A class that scrapes link preview data from a given url. Retrieves the
# image, title, description, and domain associated with the url.
class linkPreview:
    
    # Initializes the linkPreview class.
    # @param url A string containing the url to retrieve the data from.
    def __init__(self, url):
        self.url = url
        req = requests.get(url, headers)
        
        self.soup = BeautifulSoup(req.content, 'html5lib')
        
        self.image = self.findImage()
        self.title = self.findTitle()
        self.description = self.findDescription()
        self.domain = self.findDomain()
    
    # Uses BeautifulSoup to find the image associated with the url from
    # the website. First checks for Open Graph meta tags, then the shortcut icon 
    # from the website, then the first image on the webpage.
    # @return A string containing a link to the url for the image.
    def findImage(self):
        urlParse = urlparse(self.url)
        
        # If the url's protocol name (http/https) or the network location doesn't exist... 
        if len(urlParse.scheme) == 0 or len(urlParse.netloc) == 0:
            return ""
        baseUrl = urlParse.scheme + "://" + urlParse.netloc
        
        # Look for the image in <meta property="og:image" content="img.jpg">
        ret = self.soup.find('meta', attrs={'property' : 'og:image'})
        if ret is not None and 'content' in ret.attrs:
            return urljoin(baseUrl, ret['content'])
        
        # Look for the image from the shortcut icon of the website.
        ret = self.soup.find('link', attrs={'rel' : "shortcut icon"})
        if ret is not None and 'href' in ret.attrs:
            return urljoin(baseUrl, ret['href'])
        
        # Look for the image from the first image on the website.
        ret = self.soup.find('img')
        if ret is not None and 'src' in ret.attrs:
            return urljoin(baseUrl, ret['src'])
        
        return ""
    
    # Uses BeautifulSoup to find the title associated with the url from 
    # the website. First checks for Open Graph meta tags, then for a title tag.
    # If nothing is found, returns an empty string.
    # @return A string containing the title of the webpage.
    def findTitle(self):
        # Look for the title in <meta property="og:title" content="title">
        ret = self.soup.find('meta', attrs={'property': "og:title"})
        if ret is not None and 'content' in ret.attrs:
            return ret['content']
        
        # Look for the title in <title></title>
        ret = self.soup.find('title')
        if ret is not None:
            return ret.text
        
        return ""
    
    # Uses BeautifulSoup to find the description associated with the url from 
    # the website. First checks for Open Graph meta tags, then for a paragraph tag.
    # If nothing if found, returns an empty string.
    # @return A string containing the description for the webpage.
    def findDescription(self):
        # Look for the description in <meta property="og:description" content="des">
        ret = self.soup.find('meta', attrs={'property' : 'og:description'})
        if ret is not None and 'content' in ret.attrs:
            return ret['content']
        
        # Look for the description in <p></p> (first paragraph)
        bodyText = self.soup.find('body')
        if bodyText is not None:
            ret = bodyText.find('p')
            if ret is not None:
                return ret.text
        
        return ""
    
    # Uses BeautifulSoup to find the description associated with the url from 
    # the website. First checks for Open Graph meta tags, then parses the domain
    # from the url itself.
    # @return A string containing the domain of the webpage.
    def findDomain(self):
        # Look for the domain in <meta property="og:url" content="http://example.com">
        ret = self.soup.find('meta', attrs={'property' : 'og:url'})
        if ret is not None and 'content' in ret.attrs:
            urlParse = urlparse(ret['content'])
            if len(urlParse.netloc) > 0:
                return urlParse.netloc
            
        # Use input to find the domain name.
        urlParse = urlparse(self.url)
        return urlParse.netloc
