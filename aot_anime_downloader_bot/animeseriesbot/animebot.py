import requests
from os import makedirs
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib import parse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from requests.exceptions import HTTPError


# Method to create response object based on URL
def response_factory(path, selector):
    try:
        res = requests.get(path)
        res.raise_for_status()  # This will handle bad response
        elements = BeautifulSoup(res.text, 'html.parser').select(selector)
    except HTTPError as ex:
        print('Something went wrong: %s' % str(ex))
    return elements


# Method to handle selenium requests
def selenium_driver_factory(path):
    try:
        # Using headless Firefox
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options = options, executable_path=executablePath)
        driver.get(path)
    except Exception as ex:
        print('[Error URL] %s\n [Error Details] %s' % (path, str(ex)))
    return driver


def selenium_operation(path):
    driver = selenium_driver_factory(path)
    driver.find_element_by_css_selector(':not(#player)').click()
    pagesource = driver.page_source
    driver.quit()
    return pagesource


url = 'https://www6.shingekinokyojin.tv'
executablePath = 'E:/Python/geckodriver/geckodriver.exe' # For Firefox
navLinkSelector = '.main-nav a[href*="season"]'
episodeLinkSelector = '.wpex-loop-entry-title a'
iframeElementSelector = '.videoembed.activeembed iframe'
makedirs('../data/', exist_ok=True)

# Downloading HTML content
print('[Anime] Gathering Information [ %s ] ...' %url)
navElement = response_factory(url, navLinkSelector)

# Looping through each season nav links
for element in navElement:
    element_text = element.getText()
    episodeLinks = response_factory(parse.urljoin(url, element.get('href')), episodeLinkSelector)

    # Looping through all episodes in the season specific page
    for episodeLink in episodeLinks:
        # Using selenium to automate click ( To avoid ad element )
        # It will fetch page source after removing advertisement to find Video element
        page_source = selenium_operation(response_factory(episodeLink.get('href'),
                                                          iframeElementSelector)[0].get('src'))
        # Getting video contents in response
        # Stream = True will help to save file in streaming mode
        try:
            response  = requests.get(BeautifulSoup(page_source, 'html.parser')
                                     .find('video').get('src'), stream=True)
        except AttributeError as ex:
            print('No Video element found, skipping...[%s]' %episodeLink)
            continue

        # Total size of episode in bytes
        total_len = int(response.headers['content-length'])
        chunk_size = 1024 * 1024 # MegaBytes
        episodeName = [i for i in str(episodeLink.get('href')).split('/') if i][-1]

        # Saving video to a file
        with open(episodeName + '.mp4', 'wb') as file:
            progress = tqdm(iterable= response.iter_content(chunk_size= chunk_size),
                             total = total_len/chunk_size, unit='MB')
            progress.set_description(desc = '[AOT Anime] Downloading...' + episodeName, refresh=True)
            for data in progress:
                file.write(data)
            print('[AOT Anime] Downloading Completed!')
        break
    break

print('[Anime] Done...!')