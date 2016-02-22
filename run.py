#!/usr/bin/env python3
import urllib3
import xml.etree.ElementTree as ElementTree
import certifi
import csv


def get_source_xml(airline):
    """Calls the API to return the flight data for a specific Airline and return as a string

    Args:
        airline (string): The airline to request the flight data for

    Returns:
        xml_string (string): The returned xml in a decoded string form

    """

    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED', # Force certificate check.
        ca_certs=certifi.where(),  # Path to the Certifi bundle.
    )
    r = http.request('GET', "https://api.laminardata.aero/v1/airlines/" + airline +
                     "/flights?user_key=***REMOVED***")
    if r.status == 200:
        xml_string = r.data.decode("utf-8")
    else:
        xml_string = None
    return xml_string


def get_flight_data(flight_id, xml):
    tree = ElementTree.ElementTree(ElementTree.fromstring(xml))
    ElementTree.register_namespace('fx', 'http://www.fixm.aero/flight/3.0')
    ElementTree.register_namespace('fb', 'http://www.fixm.aero/base/3.0')
    root = tree.getroot()
    flight_list = root.findall("{http://www.fixm.aero/flight/3.0}Flight")

    for flight_instance in flight_list:
        flight_name = flight_instance.find("{http://www.fixm.aero/flight/3.0}flightIdentification").get("majorCarrierIdentifier")
        if flight_name == flight_id:
            return flight_instance


def get_events(xml):
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
            #actual = fix_time.find("{http://www.fixm.aero/base/3.0}actual")

            #if actual is not None:
            #    result["arrival_actual"] = actual.get("timestamp")

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

    tweet_store = open("tweets.txt", "r")
    for line in tweet_store:
        if line == message:
            print("Duplicate message. Bork.")
            tweet_store.close()
            return

    tweet_store.close()
    tweet_store = open("tweets.txt", "a")
    tweet_store.write(message)
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
    flight = "7051"
    source_xml = get_source_xml(airline)
    flight_xml = get_flight_data(airline + flight, source_xml)
    if flight_xml is not None:
        event_dict = get_events(flight_xml)
        tweet(event_dict, airline+flight)
