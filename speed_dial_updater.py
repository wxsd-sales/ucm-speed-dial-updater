from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth
import sys
import urllib3
import logging
import datetime

from zeep import Client, Settings, Plugin, xsd
from zeep import xsd
from zeep.transports import Transport
from zeep.exceptions import Fault


import os
from dotenv import load_dotenv
load_dotenv()

SPEED_DIAL_MISSING = 'N/A'

# Change to true to enable output of request/response headers and XML
DEBUG = False

LIVE = True

WSDL_FILE = 'schema/AXLAPI.wsdl'
CUCM_ADDRESS = os.getenv( "CUCM_ADDRESS" )


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

session.auth = HTTPBasicAuth( os.getenv( 'AXL_USERNAME' ), os.getenv( 'AXL_PASSWORD' ) )

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
                                f'https://{CUCM_ADDRESS}:8443/axl/' )


print('Getting list of Directory Numbers from CUCM:', CUCM_ADDRESS )
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
print('Getting list of Phones from CUCM:', CUCM_ADDRESS )
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
                print(speeddial['dirn'], 'Not found changing', speeddial['label'], 'to', SPEED_DIAL_MISSING)
                updatedSpeeddials[sdLength]['label'] = SPEED_DIAL_MISSING
                

        if requiresUpdate:
            phoneUpdates[phone] = updatedSpeeddials
            print('Phone ', phone, 'requies speeddial updatting')
        
    except Exception as err:
        print( f'\nZeep error: With getPhone: { err }' )
        sys.exit( 1 )


print(f'Updating [{len(phoneUpdates)}] Phones')

if not LIVE:
    logging.info(f'Script is not live - [{len(phoneUpdates)}] Phones Require Speeddial Updates')
    sys.exit( 1 )

logging.info(f'Updating Speeddials on [{len(phoneUpdates)}] Phones')

for phone in phoneUpdates:
    update = {'speeddial': phoneUpdates[phone]}      
    try:
        print('Updatings Phone', phone, phoneUpdates[phone])
        resp = service.updatePhone( uuid = phone, speeddials = update)
    except Exception as err:
        print( f'\nZeep error: With getPhone: { err }' )
        sys.exit( 1 )