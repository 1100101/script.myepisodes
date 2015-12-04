#!/usr/bin/env python
# -*- coding: utf-8 -*-

from BeautifulSoup import BeautifulSoup
import cookielib
import re
import urllib, urllib2, urlparse

# This is totally stolen from script.xbmc.subtitles plugin !
REGEX_EXPRESSIONS = [
    '[._ -](?:(?:(?:20|19)\d{2})[._ -])?S?(\d{1,2})(?:E|x)?(\d{2})[^\\\/]*',
    '[Ss]([0-9]+)[][._-]*[Ee]([0-9]+)([^\\\/]*)$',
    '[._ -]([0-9]+)x([0-9]+)([^\\/]*)',                     # foo.1x09
    '[._ -]([0-9]+)([0-9][0-9])([._ -][^\\/]*)',          # foo.109
    '([0-9]+)([0-9][0-9])([._ -][^\\/]*)',
    '[\\\/._ -]([0-9]+)([0-9][0-9])[^\\/]*',
    'Season ([0-9]+) - Episode ([0-9]+)[^\\/]*',              # Season 01 - Episode 02
    'Season ([0-9]+) Episode ([0-9]+)[^\\/]*',                # Season 01 Episode 02
    '[\\\/._ -][0]*([0-9]+)x[0]*([0-9]+)[^\\/]*',
    '[[Ss]([0-9]+)\]_\[[Ee]([0-9]+)([^\\/]*)',                #foo_[s01]_[e01]
    '[\._ \-][Ss]([0-9]+)[\.\-]?[Ee]([0-9]+)([^\\/]*)',       #foo, s01e01, foo.s01.e01, foo.s01-e01
    's([0-9]+)ep([0-9]+)[^\\/]*',                             #foo - s01ep03, foo - s1ep03
    '[Ss]([0-9]+)[][ ._-]*[Ee]([0-9]+)([^\\\/]*)$',
    '[\\\/._ \\[\\(-]([0-9]+)x([0-9]+)([^\\\/]*)$'
    ]

MYEPISODE_URL = "https://www.myepisodes.com"

def sanitize(title, replace):
    for char in ['[', ']', '_', '(', ')', '.', '-']:
        title = title.replace(char, replace)
    return title

def sanitize_ex(title, needlestring, replace):
    for char in needlestring:
        title = title.replace(char, replace)
    return title

class MyEpisodes(object):

    def __init__(self, userid, password):
        self.userid = userid.encode('utf-8', 'replace')
        self.password = password
        self.shows = {}
        #self.add_show_to_list('Marvels Agents Of S H I E L D', '11339')
        #self.add_show_to_list('Brooklyn Nine Nine', '12718')

        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cj)
        )
        self.opener.addheaders = [
            ('User-agent', 'Lynx/2.8.1pre.9 libwww-FM/2.14')
        ]

        login_data = urllib.urlencode({
            'username' : self.userid,
            'password' : self.password,
            'action' : "Login",
            'u': ""
            })
        login_url = "%s/%s" % (MYEPISODE_URL, "login.php?action=login")
        data = self.send_req(login_url, login_data)
        self.is_logged = True
        # Quickly check if it seems we are logged on.
        if (data is None) or (self.userid.lower() not in data.lower()):
            self.is_logged = False

    def send_req(self, url, data=None):
        try:
            response = self.opener.open(url, data)
            return ''.join(response.readlines())
        except:
            return None

    def add_show_to_list(self, showname, showid):
        sanitized_key = sanitize(showname, ' ')
        sanitized_key = sanitize_ex(sanitized_key, "\'", '')
        if sanitized_key != showname:
          showname = ";".join([showname, sanitized_key])
        self.shows[showname.lower()] = int(showid)

    def get_show_list(self):
        # Populate shows with the list of show_ids in our account
        wasted_url = "%s/%s" % (MYEPISODE_URL, "life_wasted.php")
        data = self.send_req(wasted_url)
        if data is None:
            return False
        soup = BeautifulSoup(data)
        mylist = soup.find("table", {"class": "mylist"})
        mylist_tr = mylist.findAll("tr")[1:-1]
        for row in mylist_tr:
            link = row.find('a', {'href': True})
            link_url = link.get('href')
            showid = link_url.split('/')[2]
            self.add_show_to_list(link.text.strip(), showid)
        return True

    def get_show_list_ex(self):
        # Populate shows with the list of show_ids in our account
        shows_url = "%s/%s" % (MYEPISODE_URL, "myshows/manage/")
        data = self.send_req(shows_url)
        if data is None:
            return False
        soup = BeautifulSoup(data)
        # active shows
        mylist = soup.find("select", {"id": "shows"})
        mylist_tr = mylist.findAll("option")[1:-1]
        # ignored shows
        mylist = soup.find("select", {"id": "ignored_shows"})
        mylist_tr += mylist.findAll("option")[1:-1]
        for row in mylist_tr:
            self.add_show_to_list(row.text.strip(), row['value'])
        return True

    def find_show_link(self, data, show_name, strict=False):
        if data is None:
            return None
        soup = BeautifulSoup(data)
        show_href = None
        show_name = show_name.lower()
        for link in soup.findAll("a", href=True):
            if link.string is None:
                continue
            if strict:
                if link.string.lower() == show_name:
                    show_href = link.get('href')
                    break
            else:
                if link.string.lower().startswith(show_name):
                    show_href = link.get('href')
                    break
        return show_href

    def find_show_id(self, show_name):
        # Try to find the ID of the show in our account first
        # Create a slice with only the show that may match
        slice_show = {}
        show_name = show_name.lower()
        for keys, v in self.shows.iteritems():
            if ';' in keys:
                keys = keys.split(';')
            else:
                keys = [keys,]
            for k in keys:
                if show_name in k or show_name.startswith(k):
                #if show_name in k:
                    slice_show[k] = v
        if len(slice_show) == 1:
            return slice_show.values()[0]
        # We loop through a slice containings the possibilities and we
        # search strictly for the show name.
        for key, value in slice_show.iteritems():
            if key == show_name:
                return value
        return None
        # You should really never fall there, at this point, the show should be
        # in your account, except if you disabled the feature.

        # It's not in our account yet ?
        # Try Find a show through its name and report its id
        search_data = urllib.urlencode({
            'tvshow' : show_name,
            'action' : 'Search myepisodes.com',
            })
        search_url = "%s/%s" % (MYEPISODE_URL, "search.php")
        data = self.send_req(search_url, search_data)
        show_href = self.find_show_link(data, show_name)

        if show_href is None:
            # Try to lookup the list of all the shows to find the exact title
            list_url = "%s/%s?list=%s" % (MYEPISODE_URL, "shows.php",
                                          show_name[0].upper())
            data = self.send_req(list_url)
            show_href = self.find_show_link(data, show_name, strict=True)

        # Really did not find anything :'(
        if show_href is None:
            return None

        show_url = urlparse.urlparse(show_href)
        try:
            showid = show_url.path.split('/')[2]
        except IndexError:
            return None

        if showid is None:
            return None

        return int(showid)

    # This is totally stolen from script.xbmc.subtitles plugin !
    @staticmethod
    def get_info(file_name):
        title = None
        episode = None
        season = None
        for regex in REGEX_EXPRESSIONS:
            response_file = re.findall(regex, file_name)
            # print response_file
            if len(response_file) > 0:
                season = response_file[0][0]
                episode = response_file[0][1]
            else:
                continue
            title = re.split(regex, file_name)[0]
            title = sanitize(title, ' ')
            title = title.strip()
            # print "T: %s S: %s E: %s" % (title, season, episode)
            return title.title(), season, episode            
        return None, None, None

    def add_show(self, show_id):
        # Try to add the show to your account.
        url = "%s/views.php?type=manageshow&mode=add&showid=%d" % (
            MYEPISODE_URL, show_id)
        data = self.send_req(url)
        if data is None:
            return False
        # Update list
        self.get_show_list()
        return True

    def set_episode_watched(self, show_id, season, episode):
        pre_url = "%s/myshows.php?action=Update" % MYEPISODE_URL
        seen_url = "%s&showid=%d&season=%02d&episode=%02d" % (pre_url,
                                                              show_id,
                                                              int(season),
                                                              int(episode))
        data = self.send_req("%s&seen=1" % seen_url)
        if data is None:
            return False
        return True

    def set_episode_acquired(self, show_id, season, episode):
        pre_url = "%s/myshows.php?action=Update" % MYEPISODE_URL
        acquired_url = "%s&showid=%d&season=%02d&episode=%02d&seen=0" % (pre_url,
                show_id, int(season), int(episode))
        data = self.send_req(acquired_url)
        if data is None:
            return False
        return True

