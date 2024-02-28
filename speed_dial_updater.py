
import sys
import urllib3
import logging
import datetime
import csv
import argparse
import os

from dotenv import load_dotenv
from zeep import Client, Settings, Plugin, xsd
from zeep import xsd
from zeep.transports import Transport
from zeep.exceptions import Fault
from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth

load_dotenv()



# Define our CLI argument variables
parser = argparse.ArgumentParser(prog='UCM Speed Dial Updater', 
                                 description='This Script updates the Speed Dials labels for IP Phones on your UCM Cluster by matching the Speed Dial with an Extension number')

parser.add_argument('-s', '--survey', dest='survey', action='store_true', default=False,
                    help='Create a survey of Speed Dials labels that require updating')

parser.add_argument('-b','--backup', dest='backup', action='store_true', default=True,
                    help='Create a backup of your UCM Speed dials (default: True)')

parser.add_argument('-r', '--restore', dest='restore', action='store_true',
                    help='Restore a backup of your UCM Speed dials')

parser.add_argument('-f', '--force', dest='force', action='store_true',
                    help='Perform Speed Dial updates without confirmation')

parser.add_argument('--min-digits', dest='minDigits', action='store_const', const=4,
                    help='Minimum number of Speed Dial Digits which will be updated (default: 4)')

parser.add_argument('--max-digits', dest='maxDigits', action='store_const', const=4,
                    help='Maximum number of Speed Dial Digits which will be updated (default: 4)')

parser.add_argument('--replacement-token', dest='replacementToken', action='store_const', const='N/A',
                    help='Text to replace unfound Speed Dial Extensions (default: \'N/A\')')

parser.add_argument('--ucm-address', dest='ucmAddress', action='store',
                    help='FQDN or IP Address of your UCM')

parser.add_argument('--axl-username', dest='axlUsername', action='store',
                    help='Username of your UCM AXL Account')

parser.add_argument('--axl-password', dest='axlPassword', action='store',
                    help='Password of your UCM AXL Account')

args = parser.parse_args()

print(args)

SPEED_DIAL_REPLACEMENT = args.replacementToken

# Change to true to enable output of request/response headers and XML
DEBUG = False


WSDL_FILE = 'schema/AXLAPI.wsdl'
UCM_ADDRESS = os.getenv( "UCM_ADDRESS" ) or args.ucmAddress
AXL_USERNAME = os.getenv( 'AXL_USERNAME' ) or args.axlUsername
AXL_PASSWORD = os.getenv( 'AXL_PASSWORD' ) or args.axlPassword

if UCM_ADDRESS is None:
    sys.exit('Error: Missing UCM Address in .env or argument')

if AXL_USERNAME is None:
    sys.exit('Error: Missing AXL Username in .env or argument')

if AXL_PASSWORD is None:
    sys.exit('Error: Missing AXL Password in .env or argument')

print(UCM_ADDRESS, AXL_PASSWORD, AXL_PASSWORD)

logging.basicConfig(filename=f'speeddial_updater.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# The first step is to create a SOAP client session
session = Session()

# We avoid certificate verification by default
# And disable insecure request warnings to keep the output clear
session.verify = False
urllib3.disable_warnings( urllib3.exceptions.InsecureRequestWarning )

# To enable SSL cert checking (recommended for production)
# place the CUCM Tomcat cert .pem file in the root of the project
# and uncomment the two lines below

# CERT = 'changeme.pem'
# session.verify = CERT

session.auth = HTTPBasicAuth(AXL_USERNAME, AXL_PASSWORD )

transport = Transport( session = session, timeout = 10 )

# strict=False is not always necessary, but it allows Zeep to parse imperfect XML
settings = Settings( strict = False, xml_huge_tree = True )

# If debug output is requested, add the MyLoggingPlugin callback
plugin = [ MyLoggingPlugin() ] if DEBUG else []

# Create the Zeep client with the specified settings
client = Client( WSDL_FILE, settings = settings, transport = transport,
        plugins = plugin )

# Create the Zeep service binding to AXL at the specified CUCM
service = client.create_service( '{http://www.cisco.com/AXLAPIService/}AXLAPIBinding',
                                f'https://{UCM_ADDRESS}:8443/axl/' )


print('Getting list of Directory Numbers from CUCM:', UCM_ADDRESS )

lineDict = {}

try:
    resp = service.listLine( searchCriteria = {'pattern': '%'} , returnedTags = { 'pattern': xsd.Nil , 'description': xsd.Nil} )
    lines = resp['return']['line']
    for line in lines:
        lineDict[ line['pattern']] = line['description']
except Exception as err:
    print( f'\nZeep error: With listLine: { err }' )
    sys.exit( 1 )

print(f'[{len(lineDict)}] Directory Numbers Found ')

print(lineDict)

phones = {}
print('Getting list of Phones from CUCM:', UCM_ADDRESS )
try:
    resp = service.listPhone( searchCriteria = { 'name': 'SEP%'} , returnedTags = { 'name':'', 'description': '' } )
    #print(resp['return']['phone'])
    for phone in resp['return']['phone']:
        phones[phone['uuid']] = phone['name'] + ' ' + phone['description']

except Exception as err:
    print( f'\nZeep error: With listPhone: { err }' )
    sys.exit( 1 )

print(phones)

print(f'[{len(phones)}] Phones Found')


phoneUpdates = {}

for phone in phones:
    print(phone)
    try:
        resp = service.getPhone( uuid = phone, returnedTags = {'speeddials': { 'speeddial': {'dirn': '', 'label': '', 'index': ''}}} )
        
        # Ignore phones with no speeddials
        if resp['return']['phone']['speeddials'] == None:
            continue
        print(resp['return']['phone'])
        speeddials = resp['return']['phone']['speeddials']['speeddial']
        updatedSpeeddials = []
        requiresUpdate = False
    
        # Check if each speed dial number matches a Director Number extension
        for speeddial in speeddials:
            print(speeddial['label'])
            updatedSpeeddials.append(speeddial)
            sdLength = len(updatedSpeeddials)-1
            if speeddial['dirn'] in lineDict and speeddial['label'] != lineDict[speeddial['dirn']]:
                requiresUpdate = True
                print(speeddial['dirn'], phones[phone], 'Found needs updating', speeddial['label'], 'to', lineDict[speeddial['dirn']] )
                updatedSpeeddials[sdLength]['label'] = lineDict[speeddial['dirn']]
            elif not speeddial['dirn'] in lineDict:
                requiresUpdate = True
                print(speeddial['dirn'], 'Not found changing', speeddial['label'], 'to', SPEED_DIAL_REPLACEMENT)
                updatedSpeeddials[sdLength]['label'] = SPEED_DIAL_REPLACEMENT
                

        if requiresUpdate:
            phoneUpdates[phone] = updatedSpeeddials
            print('Phone ', phone, 'requies speeddial updatting')
        
    except Exception as err:
        print( f'\nZeep error: With getPhone: { err }' )
        sys.exit( 1 )

print(f'[{len(phoneUpdates)}] Phones require updated Speed Dial Labels')

if args.survey:
    print('Survey only requested')
    with open('survey.csv', 'w') as f:  # You will need 'wb' mode in Python 2.x
        w = csv.DictWriter(f, phoneUpdates.keys())
        w.writeheader()
        w.writerow(phoneUpdates)
    sys.exit( 'Update Speed Dial Label Survey saved to Survey.csv' )


if args.backup:
    print('Creating new Backup of Speed Dials')
    with open('survey.csv', 'w') as f:  # You will need 'wb' mode in Python 2.x
        w = csv.DictWriter(f, phoneUpdates.keys())
        w.writeheader()
        w.writerow(phoneUpdates)
    sys.exit( 'Update Speed Dial Label Survey saved to Survey.csv' )



logging.info(f'Updating Speeddials on [{len(phoneUpdates)}] Phones')

def updateSpeedDial(phone, speedDials):
    print('Updating Speed Dials on Phone', phone, speedDials)
    try:
        resp = service.updatePhone( uuid = phone, speeddials = update)
    except Exception as err:
        print( f'\nZeep error: With updatePhone: { err }' )
        sys.exit( 1 )


if args.force:
    print('Force update requested, no individual confirmation will be ask')

for phone in phoneUpdates:
    update = {'speeddial': phoneUpdates[phone]}
    if not args.force:
        answer = input(f"About to update Speed Dials Phone {phone} Continue? Y/N")
        if answer.upper() in ["Y", "YES"]:
            # Do action you need
            try:
                updateSpeedDial(phone, update)
            except Exception as err:
                print( f'\nZeep error: With updatePhone: { err }' )
                sys.exit( 1 )
        elif answer.upper() in ["N", "NO"]:
            print(f'Skipping Speed Dial update for Phone {phone} ')
    else: updateSpeedDial(phone, update)
            


