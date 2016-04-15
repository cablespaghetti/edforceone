#!/usr/bin/env python3
import urllib3
import xml.etree.ElementTree as ElementTree
import certifi
import csv
import os.path
import datetime
from twython import Twython
import argparse

def check_stored_gufi():
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

    an_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
    events_map = get_events(gufi_xml)
    if events_map["last_pos_time"] is None:
        return stored_gufi
    elif (an_hour_ago > events_map["last_pos_time"]) and (an_hour_ago > events_map["arrival_estimated"]):
        print("Stored GUFI hasn't had an update in an hour and flight was supposed to land an hour ago. Not using.")
        os.remove("gufi.txt")
        return None
    else:
        return stored_gufi


def get_gufi(gufi_airline, gufi_flight):
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
    tree = ElementTree.ElementTree(ElementTree.fromstring(xml_string))
    ElementTree.register_namespace('fx', 'http://www.fixm.aero/flight/3.0')
    ElementTree.register_namespace('fb', 'http://www.fixm.aero/base/3.0')
    xml = tree.getroot()

    result = {"departure_actual": None, "departure_estimated": None, "arrival_actual": None, "arrival_estimated": None,
              "arr_aerodrome": None, "dep_aerodrome": None, "last_pos_time": None}
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

    return result


def tweet(events, flight_name):
    message = None

    if events["arrival_actual"]:
        message = flight_name + " has landed in " + get_airport(events["arr_aerodrome"]) + "."
    elif events["arrival_estimated"] and events["departure_actual"]:
        message = flight_name + " departed from " + get_airport(events["dep_aerodrome"]) + " at " + \
                  datetime.datetime.strftime(events["departure_actual"],
                                             "%H:%M:%S") + " UTC. It should arrive in " + get_airport(
            events["arr_aerodrome"]) + \
                  " at " + datetime.datetime.strftime(events["arrival_estimated"], "%H:%M:%S") + " UTC."
    elif events["departure_estimated"]:
        message = flight_name + " is scheduled to depart from " + get_airport(events["dep_aerodrome"]) + " at " + \
                  datetime.datetime.strftime(events["departure_estimated"], "%H:%M:%S") + " UTC."

    if os.path.isfile("tweets.txt") and message:
        tweet_store = open("tweets.txt", "r")
        for line in tweet_store:
            if message in line:
                print("Duplicate message. Bork.")
                tweet_store.close()
                return

        tweet_store.close()

    tweet_store = open("tweets.txt", "a")
    tweet_store.write(message + "\n")
    tweet_store.close()
    print(message)

    twitter = Twython(app_key, app_secret, oauth_token, oauth_secret)
    twitter.update_status(status=message)
    print(len(message))


def get_airport(icao):
    # Using http://openflights.org/data.html

    with open('airports.dat', encoding="latin_1", errors="ignore") as csv_file:
        reader = csv.DictReader(csv_file, fieldnames=["id", "name", "city", "country", "iata", "icao"])
        for row in reader:
            if row['icao'] == icao:
                preferred_name = row['name'] + " (" + row['city'] + "), " + row['country'] + " (" + icao + ")"
                if len(preferred_name) > 30:
                    preferred_name = row['city'] + ", " + row['country'] + " (" + icao + ")"
                    if len(preferred_name) > 30:
                        preferred_name = row['city'] + " (" + icao + ")"

                return preferred_name


if __name__ == '__main__':
    # Process the CLI arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('--laminar_key', help='A Laminar Data User Key')
    parser.add_argument('--twitter_app_key', help='A twitter app key')
    parser.add_argument('--twitter_app_secret', help='The secret for your twitter app key')
    parser.add_argument('--twitter_oauth_token', help='A twitter oauth 2 token')
    parser.add_argument('--twitter_oauth_secret', help='The secret for your twitter oauth 2 token')

    args = parser.parse_args()

    laminar_key = args.laminar_key
    app_key = args.twitter_app_key
    app_secret = args.twitter_app_secret
    oauth_token = args.twitter_oauth_token
    oauth_secret = args.twitter_oauth_secret

    if (not laminar_key) or (not app_key) or (not app_secret) or (not oauth_token) or (not oauth_secret):
        print("Error: Required parameter not set. Please use --help.")
        exit(1)

    airline = "ABD"
    flight = "666"
    gufi = get_gufi(airline, flight)
    source_xml = None

    if gufi is not None:
        source_xml = get_source_xml(gufi)

    if source_xml:
        event_dict = get_events(source_xml)
        tweet(event_dict, airline + flight)
