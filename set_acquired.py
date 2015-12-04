#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from resources.lib.myepisodes import MyEpisodes

username = "KyleK"
password = "CH]NIA3b"

if len(sys.argv) is not 2:
  print "Usage: %s <filename>" % sys.argv[0]
  sys.exit(1)

if username is "" or password is "":
  print "Username or passwor is empty!"
  sys.exit(1)

title, season, episode = MyEpisodes.get_info(sys.argv[1])

if title is None or season is None or episode is None:
  print "Unable to parse file name '%s'. Not a TV show?" % sys.argv[1]
  exit(1)

#print "Parse result: %s (S: %s E: %s)" % (title, season, episode)

mye = MyEpisodes(username, password)
if not mye.is_logged:
  print "Login to MyEpisodes.com failed!"
  sys.exit(1)

if not mye.get_show_list_ex():
  print "Could not retrieve show list!"
  sys.exit(1)

showid = mye.find_show_id(title)
if showid is None:
  print "Show '%s' is not in your personal show list, or does not exist on myepisodes.com. Skipping..." % (title)
  sys.exit(1)

print "Found : %s - %d (%sx%s)'" % (title, showid, season, episode)
if not mye.set_episode_acquired(showid, season, episode):
  print "Error setting status for show %d to 'Acquired'!" % showid
  sys.exit(1)

print "Successfully changed status for '%s %sx%s' to 'Acquired'" % (title, season, episode)

del mye
sys.exit(0)   

