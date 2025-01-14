#!/usr/bin/env python3

import argparse
import requests
import os
from ipwhois import IPWhois
import sys

sourceapp = "AS50559-DIVD_NL"

def rest_get(call,resource,retries=3):
	url = "https://stat.ripe.net/data/{}/data.json?resource={}&sourceapp={}".format(call,resource,sourceapp)
	try:
		response = requests.get(url, timeout = 1)
	except KeyboardInterrupt:
		sys.exit()
	except:
		if retries > 0:
			return rest_get(call,resource,retries-1)
		else:
			return "Timeout"
	reply = response.json()
	return reply['data']


def abuse_from_whois(ip):
	try:
		obj = IPWhois(ip)
		rdap = obj.lookup_rdap(depth=2)
		result = rdap['objects']
		abusemails = []
		for key, value in result.items():
			if value['roles'] and 'abuse' in value['roles']:
				for abusemail in value['contact']['email']:
					abusemails.append(abusemail['value'])
		mails = list(set(abusemails))
		return str(mails)[1:-1].replace(' ', '').replace("'", "")
	except KeyboardInterrupt:
		sys.exit()
	except Exception as e:
		return None

def get_info(line) :
		# Get abuse info
		# https://stat.ripe.net/data/abuse-contact-finder/data.<format>?<parameters>

		abuse_reply = rest_get("abuse-contact-finder",line)
		contacts = []
		if 'abuse_contacts' in abuse_reply:
			contacts = abuse_reply['abuse_contacts']
		if len(contacts) > 0 :
			abuse_email = contacts[0]
			abuse_source = "ripeSTAT"
		else:
			whoisabuse = abuse_from_whois(line)
			if whoisabuse:
				abuse_email = whoisabuse
				abuse_source = "whois"
			else: 
				abuse_email = "Not found"
				abuse_source = ""

		# Get ASN
		# https://stat.ripe.net/data/network-info/data.json?resource=194.5.73.5

		asn_reply = rest_get("network-info",line)
		asn = "unknown"
		prefix = "unknown"
		if 'asns' in asn_reply:
			asn = asn_reply['asns'][0]
			prefix = asn_reply['prefix']

			# Get ASN info
			if asn in asns:
				asn_data = asns[asn]
			else:
				asn_data = rest_get("as-overview",asn)
				asns[asn] = asn_data

			holder = asn_data['holder']
		else: 
			holder = "unknown"

		# Get geolocation
		if prefix != "unknown":
			if prefix in locations:
				location_data = locations[prefix]
			else:
				location_data = rest_get("maxmind-geo-lite",prefix)

			city=location_data['located_resources'][0]['locations'][0]['city']
			country=location_data['located_resources'][0]['locations'][0]['country']
		else:
			city = "unknown"
			country = "unknown"

		print('"{}","{}","{}","{}","{}","{}","{}","{}"'.format(line,abuse_email,prefix,asn,holder,country,city,abuse_source))
		if args.output :
			outfile.write('"{}","{}","{}","{}","{}","{}","{}","{}"\n'.format(line,abuse_email,prefix,asn,holder,country,city,abuse_source))
			outfile.flush()

parser = argparse.ArgumentParser(description='Get abuse and location information for IPs', allow_abbrev=False)
parser.add_argument('input', type=str, metavar="INPUT.txt", nargs="*", default="/dev/stdin", help="Either a list files with one IP address per line or a IP address [default: stdin]")
parser.add_argument('--output', "-o", type=str, metavar="OUTPUT.csv", help="output csv file")
args = parser.parse_args()

if isinstance(args.input,str):
	files = [args.input]
else :
	files = args.input
asns = {}
locations = {}

if args.output :
	outfile = open(args.output,"w")

if args.output :
	outfile.write('ip,abuse,prefix,asn,holder,country,city,abuse_source\n')
	outfile.flush()
print('ip,abuse,prefix,asn,holder,country,city,abuse_source')
sys.stdout.flush()
for f in files:
	if os.path.isfile(f):
		file = open(f,"r")
		for line in file.readlines():
			line = line.strip()
			get_info(line)
		file.close()
	else:
		get_info(f)


