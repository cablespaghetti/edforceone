Ed Force One [![Build Status](https://travis-ci.org/cablespaghetti/edforceone.svg?branch=develop)](https://travis-ci.org/cablespaghetti/edforceone)
============

A simple app that uses the [Laminar Data](https://developer.laminardata.aero) API to post to [a Twitter feed](https://twitter.com/edforceupdates) about the locations of Iron Maiden's tour plane.

Requirements
============

Slumber requires the following modules.

* Python 3.5+ (although it may run on older)
* certifi
* urllib3
* twython

Usage
=====
```
python3 run.py --laminar_key xxxx --twitter_app_key xxxx --twitter_app_secret xxxx --twitter_oauth_token xxxx --twitter_oauth_secret xxxx
```

TODO
====
Must
----
* Make sure we don't tweet more than once when data changes (e.g. take offs)
* #EdForceOne hashtag on messages for greater exposure

Should
------
* Use Laminar's aerodromes API instead of dat file
* Use something more sophisticated for message history persistence

Could
-----
* Get the app to tweet an arrival when laminar doesn't get one
