#!/usr/bin/env python3
import urllib3
import xml.etree.ElementTree as ElementTree
import certifi
import csv
import os.path
import datetime
from twython import Twython
import argparse
import calendar
import time

def check_stored_gufi():
    # Read
    if os.path.isfile("gufi.txt"):
        print("Stored GUFI found")
        gufi_store = open("gufi.txt", "r")
        stored_gufi = gufi_store.readline().rstrip()
        gufi_store.close()
    else:
        return None

    gufi_xml = get_source_xml(stored_gufi)
    if gufi_xml is not None:
        print("Stored GUFI " + stored_gufi + " still works.")
    else:
        os.remove("gufi.txt")
        return None

    return stored_gufi


def get_gufi(gufi_airline, gufi_flight, laminar_key):
    current_gufi = check_stored_gufi()

    if current_gufi is not None:
        return current_gufi

    print("No working stored GUFI. Getting a fresh one.")
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',  # Force certificate check.
        ca_certs=certifi.where(),  # Path to the Certifi bundle.
    )
    r = http.request('GET', "https://api.laminardata.aero/v1/airlines/" + gufi_airline +
                     "/flights?user_key=" + laminar_key)
    if r.status == 200:
        xml_string = r.data.decode("utf-8")
    else:
        print("Flight not returned")
        return None

    tree = ElementTree.ElementTree(ElementTree.fromstring(xml_string))
    ElementTree.register_namespace('fx', 'http://www.fixm.aero/flight/3.0')
    ElementTree.register_namespace('fb', 'http://www.fixm.aero/base/3.0')
    root = tree.getroot()
    flight_list = root.findall("{http://www.fixm.aero/flight/3.0}Flight")

    most_recent_timestamp = None

    for flight_instance in flight_list:
        flight_name = flight_instance.find("{http://www.fixm.aero/flight/3.0}flightIdentification").get(
            "majorCarrierIdentifier")
        if flight_name == (gufi_airline + gufi_flight):
            flight_timestamp = datetime.datetime.strptime(flight_instance.get("timestamp")[:-5], "%Y-%m-%dT%H:%M:%S")
            if (most_recent_timestamp is None) or (flight_timestamp > most_recent_timestamp):
                most_recent_timestamp = flight_timestamp
                current_gufi = flight_instance.find("{http://www.fixm.aero/flight/3.0}gufi").text
                gufi_store = open("gufi.txt", "w")
                gufi_store.write(gufi)
                gufi_store.close()

    return current_gufi


def get_source_xml(flight_gufi):
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',  # Force certificate check.
        ca_certs=certifi.where(),  # Path to the Certifi bundle.
    )
    r = http.request('GET', "https://api.laminardata.aero/v1/flights/" + flight_gufi + "?user_key=" + laminar_key)
    if r.status == 200:
        xml_string = r.data.decode("utf-8")
    else:
        xml_string = None
    return xml_string


def get_events(xml_string):
    try:
        result = {"departure_actual": None, "departure_estimated": None, "arrival_actual": None,
                  "arrival_estimated": None,
                  "arr_aerodrome": None, "dep_aerodrome": None, "last_pos_time": None}
        tree = ElementTree.ElementTree(ElementTree.fromstring(xml_string))
        ElementTree.register_namespace('fx', 'http://www.fixm.aero/flight/3.0')
        ElementTree.register_namespace('fb', 'http://www.fixm.aero/base/3.0')
        xml = tree.getroot()


        departures = xml.findall("{http://www.fixm.aero/flight/3.0}departure")
        arrivals = xml.findall("{http://www.fixm.aero/flight/3.0}arrival")
        enroute = xml.find("{http://www.fixm.aero/flight/3.0}enRoute")

        if enroute:
            position_element = enroute.find("{http://www.fixm.aero/flight/3.0}position")
            if position_element is not None:
                result["last_pos_time"] = datetime.datetime.strptime(position_element.get("positionTime")[:-5],
                                                                     "%Y-%m-%dT%H:%M:%S")

        if departures:
            for departure in departures:
                fix_time = departure.find("{http://www.fixm.aero/flight/3.0}departureFixTime")
                dep_aerodrome_element = departure.find("{http://www.fixm.aero/flight/3.0}departureAerodrome")
                estimated = fix_time.find("{http://www.fixm.aero/base/3.0}estimated")
                actual = fix_time.find("{http://www.fixm.aero/base/3.0}actual")

                if actual is not None:
                    result["departure_actual"] = datetime.datetime.strptime(actual.get("timestamp")[:-5],
                                                                            "%Y-%m-%dT%H:%M:%S")

                if estimated is not None:
                    result["departure_estimated"] = datetime.datetime.strptime(estimated.get("timestamp")[:-5],
                                                                               "%Y-%m-%dT%H:%M:%S")

                if dep_aerodrome_element is not None:
                    result["dep_aerodrome"] = dep_aerodrome_element.get("code")

        if arrivals:
            for arrival in arrivals:
                fix_time = arrival.find("{http://www.fixm.aero/flight/3.0}arrivalFixTime")
                arr_aerodrome_element = arrival.find("{http://www.fixm.aero/flight/3.0}arrivalAerodrome")
                arr_aerodrome_orig_element = arrival.find("{http://www.fixm.aero/flight/3.0}arrivalAerodromeOriginal")
                estimated = fix_time.find("{http://www.fixm.aero/base/3.0}estimated")
                actual = fix_time.find("{http://www.fixm.aero/base/3.0}actual")

                if actual is not None:
                    result["arrival_actual"] = datetime.datetime.strptime(actual.get("timestamp")[:-5], "%Y-%m-%dT%H:%M:%S")

                if estimated is not None:
                    result["arrival_estimated"] = datetime.datetime.strptime(estimated.get("timestamp")[:-5],
                                                                             "%Y-%m-%dT%H:%M:%S")

                if arr_aerodrome_element is not None:
                    result["arr_aerodrome"] = arr_aerodrome_element.get("code")
                elif arr_aerodrome_orig_element is not None:
                    result["arr_aerodrome"] = arr_aerodrome_orig_element.get("code")
    except Exception:
        print("Error: Something bad happened")

    return result


def tweet(events, flight_name, tweet=False):
    message = None
    flight_state = None

    if events["arrival_actual"]:
        message = flight_name + " has landed in " + get_airport(events["arr_aerodrome"]) + "."
        flight_state = "landed"
    elif events["arrival_estimated"] and events["departure_actual"]:
        message = flight_name + " departed from " + get_airport(events["dep_aerodrome"]) + " at " + \
                  datetime.datetime.strftime(events["departure_actual"],
                                             "%H:%M:%S") + " UTC. It should arrive in " + get_airport(
            events["arr_aerodrome"]) + \
                  " at " + datetime.datetime.strftime(events["arrival_estimated"], "%H:%M:%S") + " UTC."
        flight_state = "airborne"
    elif events["departure_estimated"]:
        message = flight_name + " is scheduled to depart from " + get_airport(events["dep_aerodrome"]) + " at " + \
                  datetime.datetime.strftime(events["departure_estimated"], "%H:%M:%S") + " UTC."
        flight_state = "scheduled"

    message += " #EdForceOne"

    if not flight_state:
        print("No valid flight state. Something has gone wrong.")
        return None

    if os.path.isfile("tweets.txt") and message:
        tweet_store = open("tweets.txt", "r")
        for line in tweet_store:
            if len(line) > 10:
                if int(line[:10]) > (calendar.timegm(time.gmtime()) - 86400):
                    if (events["dep_aerodrome"] in line) and (flight_state in line):
                        print("Duplicate message. Bork.")
                        tweet_store.close()
                        return "Duplicate"

        tweet_store.close()

    tweet_store = open("tweets.txt", "a")
    current_epoch = calendar.timegm(time.gmtime())
    tweet_store.write(str(current_epoch) + " " + events["dep_aerodrome"] + " " + flight_state + "\n")
    tweet_store.close()
    print(message)

    if tweet is True:
        twitter = Twython(app_key, app_secret, oauth_token, oauth_secret)
        twitter.update_status(status=message)
        print(len(message))

    return message

def get_airport(icao):
    # Using http://openflights.org/data.html

    with open('edforceone/airports.dat', encoding="latin_1", errors="ignore") as csv_file:
        reader = csv.DictReader(csv_file, fieldnames=["id", "name", "city", "country", "iata", "icao"])
        for row in reader:
            if row['icao'] == icao:
                preferred_name = row['name'] + " (" + row['city'] + "), " + row['country'] + " (" + icao + ")"
                if len(preferred_name) > 18:
                    preferred_name = row['city'] + ", " + row['country'] + " (" + icao + ")"
                    if len(preferred_name) > 18:
                        preferred_name = row['city'] + " (" + icao + ")"
                        if len(preferred_name) > 18:
                            preferred_name = row['city']
                            if len(preferred_name) > 18:
                                preferred_name = icao

                return preferred_name


if __name__ == '__main__':
    # Process the CLI arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('--laminar_key', help='A Laminar Data User Key')
    parser.add_argument('--twitter_app_key', help='A twitter app key')
    parser.add_argument('--twitter_app_secret', help='The secret for your twitter app key')
    parser.add_argument('--twitter_oauth_token', help='A twitter oauth 2 token')
    parser.add_argument('--twitter_oauth_secret', help='The secret for your twitter oauth 2 token')
    parser.add_argument('--tweet', help='Set to True if you want to tweet')

    args = parser.parse_args()

    laminar_key = args.laminar_key
    app_key = args.twitter_app_key
    app_secret = args.twitter_app_secret
    oauth_token = args.twitter_oauth_token
    oauth_secret = args.twitter_oauth_secret
    if args.tweet == "True":
        args_tweet = True
    else:
        args_tweet = False

    if (not laminar_key) or (not app_key) or (not app_secret) or (not oauth_token) or (not oauth_secret):
        print("Error: Required parameter not set. Please use --help.")
        exit(1)

    airline = "ABD"
    flight = "666"
    gufi = get_gufi(airline, flight, laminar_key)
    source_xml = None

    if gufi is not None:
        source_xml = get_source_xml(gufi)

    if source_xml:
        event_dict = get_events(source_xml)
        tweet(event_dict, airline + flight, args_tweet)
