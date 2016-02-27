#!/usr/bin/env python3
import urllib3
import xml.etree.ElementTree as ElementTree
import certifi
import csv
import os.path


def check_stored_gufi():
   gufi = None

   if os.path.isfile("gufi.txt"):
       print("Stored GUFI found")
       gufi_store = open("gufi.txt", "r")
       gufi = gufi_store.readline().rstrip()
       gufi_store.close()
   else:
       return None

   if get_source_xml(gufi) is not None:
       print("Stored GUFI " + gufi + " still works.")
       return gufi
   else:
       return None


def get_gufi(airline, flight):
    gufi = check_stored_gufi()

    if gufi is not None:
        return gufi

    print("No working stored GUFI. Getting a fresh one.")
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED', # Force certificate check.
        ca_certs=certifi.where(),  # Path to the Certifi bundle.
    )
    r = http.request('GET', "https://api.laminardata.aero/v1/airlines/" + airline +
                     "/flights?user_key=***REMOVED***")
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

    for flight_instance in flight_list:
        flight_name = flight_instance.find("{http://www.fixm.aero/flight/3.0}flightIdentification").get("majorCarrierIdentifier")
        if flight_name == (airline + flight):
            gufi = flight_instance.find("{http://www.fixm.aero/flight/3.0}gufi").text
            gufi_store = open("gufi.txt", "w")
            gufi_store.write(gufi)
            gufi_store.close()
            return gufi

    return None


def get_source_xml(gufi):
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED', # Force certificate check.
        ca_certs=certifi.where(),  # Path to the Certifi bundle.
    )
    r = http.request('GET', "https://api.laminardata.aero/v1/flights/" + gufi + "?user_key=***REMOVED***")
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
              "arr_aerodrome": None, "dep_aerodrome": None}
    departures = xml.findall("{http://www.fixm.aero/flight/3.0}departure")
    arrivals = xml.findall("{http://www.fixm.aero/flight/3.0}arrival")

    if departures:
        for departure in departures:
            fix_time = departure.find("{http://www.fixm.aero/flight/3.0}departureFixTime")
            dep_aerodrome_element = departure.find("{http://www.fixm.aero/flight/3.0}departureAerodrome")
            estimated = fix_time.find("{http://www.fixm.aero/base/3.0}estimated")
            actual = fix_time.find("{http://www.fixm.aero/base/3.0}actual")

            if actual is not None:
                result["departure_actual"] = actual.get("timestamp")

            if estimated is not None:
                result["departure_estimated"] = estimated.get("timestamp")

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
                result["arrival_actual"] = actual.get("timestamp")

            if estimated is not None:
                result["arrival_estimated"] = estimated.get("timestamp")

            if arr_aerodrome_element is not None:
                result["arr_aerodrome"] = arr_aerodrome_element.get("code")
            elif arr_aerodrome_orig_element is not None:
                result["arr_aerodrome"] = arr_aerodrome_orig_element.get("code")

    return result


def tweet(events, flight_name):
    if events["arrival_actual"]:
        message = flight_name + " has landed in " + get_airport(events["arr_aerodrome"]) + "."
    elif events["arrival_estimated"] and events["departure_actual"]:
        message = flight_name + " departed from " + get_airport(events["dep_aerodrome"]) + " at " + \
                  events["departure_actual"] + ". It should arrive in " + get_airport(events["arr_aerodrome"]) + \
                  " at " + events["arrival_estimated"] + "."
    elif events["departure_estimated"]:
        message = flight_name + " is scheduled to depart from " + get_airport(events["dep_aerodrome"]) + " at " + \
                  events["departure_estimated"] + "."

    if os.path.isfile("tweets.txt"):
        tweet_store = open("tweets.txt", "r")
        for line in tweet_store:
            if message in line:
                print("Duplicate message. Bork.")
                tweet_store.close()
                return
            else:
                tweet_store.close()

    tweet_store = open("tweets.txt", "a")
    tweet_store.write(message + "\n")
    tweet_store.close()
    print(message)


def get_airport(icao):
# Using http://openflights.org/data.html

    with open('airports.dat', encoding="latin_1", errors="ignore") as csv_file:
        reader = csv.DictReader(csv_file, fieldnames=["id", "name", "city", "country", "iata", "icao"])
        for row in reader:
            if row['icao'] == icao:
                #if row['city'] not in row['name']:
                #    return row['name'] + " (" + row['city'] + "), " + row['country'] + " (" + icao + ")"
                #else:
                    return row['city'] + ", " + row['country'] + " (" + icao + ")"


if __name__ == '__main__':
    airline = "BEE"
    flight = "103"
    gufi = get_gufi(airline, flight)
    if gufi is not None:
        source_xml = get_source_xml(gufi)
    if source_xml is not None:
        event_dict = get_events(source_xml)
        tweet(event_dict, airline+flight)
