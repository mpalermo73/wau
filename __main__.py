
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

if sys.version_info[0] != 3:
    raise Exception("Must be using Python 3")

debugme = False

bs = bs4.BeautifulSoup
pp = pprint.PrettyPrinter(indent=4, depth=6)

theseargs = {}

###########################
def dump_help(theseargs):

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

    if len(theseargs['args']) < 3: dump_help(theseargs)

    if debugme: print("CMD: " + str(theseargs['args']))

    args = theseargs['args']

    options, remainder = getopt.getopt(args[1:], 'c:hd', ['config=', 'help', 'debug'])

    for opt, arg in options:

        if opt in ('-h', '--help'):
            if debugme: print("FOUND help: " + str(arg))
            dump_help(theseargs)

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
        config_loaded = False
        dump_help(theseargs)

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
def build_remote_info():

    global debugme

    if debugme: print("DEF: "+ str(inspect.stack()[0][3]))

    if debugme: print("build_remote_info")

    user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 13.3; rv:66.0)'}

    # Open Communication
    # response = get_url(addon.url_project)
    response = requests.get(addon.url_project, headers=user_agent)
    # response = requests.get(addon.url_project, headers=user_agent, allow_redirects=False)
    #
    # if "Location" in response.headers:
    #     print("REDIRECT: "+ str(response.headers['Location']))
    #     addon.url_real = response.headers['Location']
    # else:
    #     print("NORMAL: "+ str(url))
    #     addon.url_real = addon.url_project

    response.close()


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

    # return addon
###########################


###########################
def get_remote_file_info():

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

    # return addon
###########################


###########################
def get_local_addon_info():

    global debugme

    if debugme: print("DEF: "+ str(inspect.stack()[0][3]))

    if os.path.isfile(addon.stamp_file):
        addon.date_local = int(os.path.getmtime(addon.stamp_file))
        addon.date_local_utc = addon.date_local + int(time.timezone)
        if debugme: print ("stamp_file: \""+ str(addon.stamp_file) +"\" EXISTS")
    else:
        addon.date_local = int(0)
        addon.date_local_utc = int(0)
        if debugme: print("stamp_file: \"" + str(addon.stamp_file) + "\" NOT FOUND")

    # print("MTIME: \"" + str(addon.date_local))
###########################


###########################
def update_time_stamps(zip_contents):

    global debugme

    if debugme: print("DEF: " + str(inspect.stack()[0][3]))

    dirs = []

    fh = open(addon.stamp_file, 'w')

    fh.writelines(addon.version +"\n")

    with zipfile.ZipFile(zip_contents, 'r') as z:
        for F in z.namelist():
            fh.writelines(F +"\n")

            if F.split('/')[0] not in dirs:
                dirs.append(str(F.split('/')[0]))

    fh.close()

    os.utime(addon.stamp_file, (addon.date_remote_utc, addon.date_remote_utc))
    if debugme: print("STAMPED: " + str(addon.stamp_file))

    for dir in dirs:
        os.utime(addon.tank +"/"+ dir, (addon.date_remote_utc, addon.date_remote_utc))
        if debugme: print("STAMPED: "+ str(addon.tank +"/"+ dir))
###########################


###########################
def get_addon_package():

    global debugme

    if debugme: print("DEF: " + str(inspect.stack()[0][3]))

    request = requests.get(addon.url_file_direct)
    addon_zip = zipfile.ZipFile(io.BytesIO(request.content))
    addon_zip.extractall(path=str(addon.tank))

    update_time_stamps(io.BytesIO(request.content))
###########################


###########################
if __name__ == '__main__':

    theseargs['args'] = sys.argv

    config = parse_cmd_args(theseargs)

    if "addons" in config.keys() and "curse" in config['addons'].keys():

        if debugme:
            print("MAIN: "+ str(config.keys()))
            print("CURSE: "+ str(config['addons'].keys()))

        curse_addons = config['addons']['curse']
        other_addons = config['addons']['other']
    else:
        print("CONFIG BUSTED")
        print("MAIN: "+ str(config.keys()))
        print("CURSE: "+ str(config['addons'].keys()))
        exit(1)

    if debugme: print("curse_addons: " + str(curse_addons))
    if debugme: print("other_addons: " + str(other_addons))
    if debugme: print("addon_directory: " + str(config['addon_directory']))

    for ca in sorted(curse_addons):
        if debugme: print("ca: " + str(ca))

        # init this addon
        addon = CurseAddon(config, ca)

        # Get any local addon info
        get_local_addon_info()

        # Get remote addon info
        build_remote_info()

        # Get addon file info
        get_remote_file_info()

        # check for freshness
        if addon.check_freshness():
            print("UPDATE: "+ str(addon.title) +" - remote: "+ str(human_time(addon.date_remote_utc)) +" > local: "+ str(human_time(addon.date_local_utc)))
            get_addon_package()
        else:
            print("CURRENT: " + str(addon.title) + " - remote: " + str(human_time(addon.date_remote_utc)) + " <= local: " + str(human_time(addon.date_local_utc)))

        # Dump vars
        print(pp.pprint(str(vars(addon))))

        print("=========")

