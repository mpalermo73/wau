
# https://youtu.be/v5DDW5dyfyc?t=141

from library import CurseAddon

import bs4
import getopt
import os
import pprint
import requests
import sys
import time
import yaml
import inspect
import zipfile
import io

if sys.version_info[0] != 3: raise Exception("Must be using Python 3")

global debugme
debugme = False

bs = bs4.BeautifulSoup
pp = pprint.PrettyPrinter(indent=4, depth=6)

theseargs = {}

###########################
def dumpHelp(theseargs):

    if 'error' in theseargs and theseargs['error']:
        print("")
        print(theseargs['error'])

    print("")
    print("-c --config\tYour config file")
    print("-d --debug\tVerbose output")
    print("-h --help\tThis help message")
    print("")
    exit(1)
###########################


###########################
def human_time(epoch):
    return str(time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime(epoch)))
###########################


###########################
def parse_cmd_args(theseargs):

    global debugme

    if debugme: print("DEF: "+ str(inspect.stack()[0][3]))

    theseargs['debugme'] = False

    if len(theseargs['args']) < 3: dumpHelp(theseargs)

    if debugme: print("CMD: " + str(theseargs['args']))

    args = theseargs['args']

    options, remainder = getopt.getopt(args[1:], 'c:hd', ['config=', 'help', 'debug'])

    for opt, arg in options:

        if opt in ('-h', '--help'):
            if debugme: print("FOUND help: " + str(arg))
            dumpHelp()

        elif opt in ('-d', '--debug'):
            if debugme: print("FOUND debug: ")
            theseargs['debugme'] = True
            debugme = True

        if opt in ('-c', '--config'):
            if debugme: print("FOUND config: " + str(arg))
            theseargs['config_file'] = str(arg)

    if os.path.isfile(theseargs['config_file']):
        config_loaded = yaml.load(open(theseargs['config_file']))
    else:
        theseargs['error'] = "Missing Config"
        dumpHelp(theseargs)

    # print({"config_loaded: " + str(config_loaded)})

    return config_loaded

###########################


###########################
def get_url(url):

    global debugme

    if debugme: print("DEF: "+ str(inspect.stack()[0][3]))

    if debugme: print("get_url: "+ str(url))

    user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 13.3; rv:66.0)'}

    response = requests.get(url, headers=user_agent)
    response.close()
    return response
###########################


###########################
def build_remote_info(addon):
    
    global debugme

    if debugme: print("DEF: "+ str(inspect.stack()[0][3]))

    if debugme: print("build_remote_info")

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
    
    global debugme

    if debugme: print("DEF: "+ str(inspect.stack()[0][3]))

    if debugme: print("get_remote_file_info")

    # Get headers of addon zip file
    response_file = requests.get(addon.url_download, stream=True).headers

    # print(str(response_file))

    # Thu, 14 Dec 2017 07:31:54 GMT
    file_date_format = '%a, %d %b %Y %H:%M:%S %Z'

    addon.size_remote = response_file['Content-Length']
    addon.date_remote_utc = int(time.mktime(time.strptime(response_file['Last-Modified'], file_date_format)))
    addon.url_file_direct = requests.get(addon.url_download, stream=True).url

    return addon
###########################


###########################
def get_local_addon_info(addon):

    global debugme

    if debugme: print("DEF: "+ str(inspect.stack()[0][3]))

    # stamp_file = str(addon.tank) +"/."+ str(addon.name)

    if os.path.isfile(addon.stamp_file):
        addon.date_local = int(os.path.getmtime(addon.stamp_file))
        addon.date_local_utc = addon.date_local + int(time.timezone)
        print ("stamp_file: \""+ str(addon.stamp_file) +"\" EXISTS")
    else:
        addon.date_local = int(0)
        addon.date_local_utc = int(0)
        print("stamp_file: \"" + str(addon.stamp_file) + "\" NOT FOUND")

    # print("MTIME: \"" + str(addon.date_local))
###########################


###########################
def update_stamp_file(addon, zip_contents):

    global debugme

    if debugme: print("DEF: " + str(inspect.stack()[0][3]))

    fh = open(addon.stamp_file, 'w')

    fh.writelines(addon.version +"\n")

    with zipfile.ZipFile(zip_contents, 'r') as zip:
        for F in zip.namelist():
            fh.writelines(F +"\n")

    fh.close()
###########################


###########################
def get_addon_package(addon):

    global debugme

    if debugme: print("DEF: " + str(inspect.stack()[0][3]))

    request = requests.get(addon.url_file_direct)
    addon_zip = zipfile.ZipFile(io.BytesIO(request.content))
    addon_zip.extractall(path=str(addon.tank))

    update_stamp_file(addon, io.BytesIO(request.content))

    addon_zip = None
    request = None
###########################


###########################
if __name__ == '__main__':

    theseargs['args'] = sys.argv

    config = parse_cmd_args(theseargs)

    curse_addons = config['addons']['curse']
    other_addons = config['addons']['other']

    if debugme: print("curse_addons: " + str(curse_addons))
    if debugme: print("other_addons: " + str(other_addons))
    if debugme: print("addon_directory: " + str(config['addon_directory']))

    for ca in curse_addons:
        if debugme: print("ca: " + str(ca))

        addon = CurseAddon()

        addon.name = str(ca.lower())

        addon.tank = config['addon_directory']
        if debugme: print("tank: " + str(addon.tank))

        addon.stamp_file = str(addon.tank) + "/." + str(addon.name)
        if debugme: print("tank: " + str(addon.stamp_file))

        # Get local addon info
        get_local_addon_info(addon)

        # quit()

        # Make URL for this addon
        addon.url_project = str(addon.url_base +"/"+ str(ca))
        if debugme: print("url_project: " + str(addon.url_project))

        # Get addon info
        addon = build_remote_info(addon)

        # Get addon file info
        get_remote_file_info(addon)

        print(pp.pprint(str(vars(addon))))

        # Compare times
        if addon.date_remote_utc > addon.date_local_utc:
            print("UPDATE: "+ str(addon.title) +" - "+ str(human_time(addon.date_remote_utc)) +" > "+ str(human_time(addon.date_local_utc)))
            get_addon_package(addon)
        else:
            print("CURRENT: " + str(addon.title) + " - " + str(human_time(addon.date_remote_utc)) + " <= " + str(human_time(addon.date_local_utc)))

        # Dump vars
        # print(pp.pprint(str(vars(addon))))

        print("=========")

