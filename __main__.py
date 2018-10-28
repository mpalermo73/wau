
# https://youtu.be/v5DDW5dyfyc?t=141
from typing import List

from library import CurseAddon

import bs4
import os
import pprint
import requests
import time

debugme = False
bs = bs4.BeautifulSoup
pp = pprint.PrettyPrinter(indent=4, depth=6)

tank = str(os.path.expanduser("~") + "/Games/Warcraft_Addons")

curse_addons: List[str] = [
    "undermine-journal",
    "gathermate2"
    ]

###########################
def get_url(url):
    
    print("get_url: "+ str(url))

    user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 13.3; rv:66.0)'}

    response = requests.get(url, headers=user_agent)
    response.close()
    return response
###########################


###########################
def build_remote_info(addon):
    
    print("build_remote_info")

    # Open Communication
    response = get_url(addon.url_project)

    # Some things still redirect to WoWAce
    addon.url_real = response.url
    if debugme: print("url_real: " + str(addon.url_real))

    # Get Raw HTML
    html_raw = bs(response.text, 'html.parser')

    # Pretty Title
    html_title_raw = str(html_raw.title.string)
    # print("html_title_raw: " + str(html_title_raw.split(' - ')[1]))
    addon.title = str(html_title_raw.split(' - ')[1])
    if debugme: print("title: " + str(addon.title))

    # Get version
    s1 = html_raw.find_all('a', attrs={'class': 'overflow-tip'})
    addon.version = str(s1[0]['data-name'])
    if debugme: print("addon.version: " + str(addon.version))

    # Get "Release" download link
    s1 = html_raw.find_all('a', attrs={'class': 'icon-only'})
    addon.url_download = str(addon.url_real + "/" + '/'.join(s1[0]['href'].split('/')[3:]))
    if debugme: print("addon.url_download: " + str(addon.url_download))

    return addon
###########################


###########################
def get_remote_file_info(addon):
    
    print("get_remote_file_info")

    # Get headers of addon zip file
    response_file = requests.get(addon.url_download, stream=True).headers

    # Thu, 14 Dec 2017 07:31:54 GMT
    file_date_format = '%a, %d %b %Y %H:%M:%S %Z'

    addon.size_remote = response_file['Content-Length']
    addon.date_remote = int(time.mktime(time.strptime(response_file['Last-Modified'], file_date_format)))
    addon.url_file_direct = requests.get(addon.url_download, stream=True).url

    return addon
###########################


###########################
if __name__ == '__main__':
    # print("loaded " + str(os.path.basename(__file__)))

    for ca in curse_addons:
        if debugme: print("ca: " + str(ca))

        addon = CurseAddon()

        # Addon tank
        addon.tank = str(os.path.expanduser("~") + str(tank))
        if debugme: print("tank: " + str(addon.tank))

        # Make URL for this addon
        addon.url_project = str(addon.url_base +"/"+ str(ca))
        if debugme: print("url_project: " + str(addon.url_project))

        # Get addon info
        addon = build_remote_info(addon)

        # Get addon file info
        get_remote_file_info(addon)

        # Dump vars
        print(pp.pprint(str(vars(addon))))

        print("=========")

