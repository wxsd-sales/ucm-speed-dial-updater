import sys
import urllib3
from zeep import Client, Settings, xsd
from zeep import xsd
from zeep.transports import Transport
from zeep.exceptions import Fault
from requests import Session
from requests.auth import HTTPBasicAuth
from pathlib import Path
from debugger import DebugLogger
from prettytable import PrettyTable


class UCMConnection:

    """This is a test class for dataclasses.

    This is the body of the docstring description.

    Args:
        var_int (int): An integer.
        var_str (str): A string.

    """

    ucmAddress: str

    def __init__(self, ucmAddress, axlUsername, axlPassword, wsdlFile, debug = False, soapDebug=False):

        if debug:
            print('Creating Connection:', ucmAddress, axlUsername, wsdlFile, debug, soapDebug )
        self.debug = debug
        self.ucmAddress = ucmAddress


        # The first step is to create a SOAP client session
        self.session = Session()

        # We avoid certificate verification by default
        # And disable insecure request warnings to keep the output clear
        self.session.verify = False
        urllib3.disable_warnings( urllib3.exceptions.InsecureRequestWarning )

        # To enable SSL cert checking (recommended for production)
        # place the CUCM Tomcat cert .pem file in the root of the project
        # and uncomment the two lines below

        # CERT = 'changeme.pem'
        # session.verify = CERT

        self.session.auth = HTTPBasicAuth(axlUsername, axlPassword )

        transport = Transport( session = self.session, timeout = 10 )

        # strict=False is not always necessary, but it allows Zeep to parse imperfect XML
        settings = Settings( strict = False, xml_huge_tree = True )

        # If debug output is requested, add the MyLoggingPlugin callback
        plugin = [ DebugLogger() ] if soapDebug else []

        # Create the Zeep client with the specified settings
        client = Client( wsdlFile, settings = settings, transport = transport,
                plugins = plugin )

        # Create the Zeep service binding to AXL at the specified CUCM
        self.service = client.create_service( '{http://www.cisco.com/AXLAPIService/}AXLAPIBinding',
                                        f'https://{ucmAddress}:8443/axl/' )
        
    def getDirectoryNumbers(self):
        directoryNumbers = {}
        # Query all Directory Numbers on the UCM
        try:
            resp = self.service.listLine( searchCriteria = {'pattern': '%'} , returnedTags = { 'pattern': xsd.Nil , 'description': xsd.Nil} )
            lines = resp['return']['line']
            for line in lines:
                directoryNumbers[ line['pattern']] = line['description']
        except Exception as err:
            print( f'\nZeep error: With listLine: { err }' )
            sys.exit( 1 )

        return directoryNumbers


    def getPhones(self):
        phones = {}
        print('Getting list of Phones from CUCM:', self.ucmAddress )
        try:
            resp = self.service.listPhone( searchCriteria = { 'name': 'SEP%'} , returnedTags = { 'name':'', 'description': '' } )
            for phone in resp['return']['phone']:
                newEntry = {
                    'name': phone['name'],
                    'description': phone['description']
                }
                phones[phone['uuid']] = newEntry

        except Exception as err:
            print( f'\nZeep error: With listPhone: { err }' )
            sys.exit( 1 )

        return phones

    def getPhoneSpeedDials(self, phone):

        try:
            resp = self.service.getPhone( uuid = phone, returnedTags = {'speeddials': { 'speeddial': {'dirn': '', 'label': '', 'index': ''}}} )
            if resp['return']['phone']['speeddials']:
                return resp['return']['phone']['speeddials']['speeddial']
            else:
                return None

        except Exception as err:
            print( f'\nZeep error: With getPhone: { err }' )
            sys.exit( 1 )


    def getAllPhonesWithSpeedDials(self):
        
        phoneSpeedDials = {}
        phones = self.getPhones()
      
        for phone in phones:
            speedDials = self.getPhoneSpeedDials(phone)
            if speedDials:
                newEntry = {"speedDials":speedDials}
                newEntry.update(phones[phone])
                phoneSpeedDials[phone] = newEntry
        return phoneSpeedDials
    
    def updatePhoneSpeedDial(self, phone, speedDials):
        if self.debug:
            print('Updating Speed Dials on Phone')
            print(phone, type(phone), len(phone))
            print(speedDials,  type(speedDials))
            print(self.service)
            self.getPhoneSpeedDials(phone)

        try:
            if phone and speedDials:
                resp = self.service.updatePhone( uuid = phone, speeddials = speedDials)
        except Exception as err:
            print( f'\nZeep error: With updatePhone: { err }' )
            sys.exit( 1 )
    
    def updateSpeedDials(self, newSpeedDials, force=True):
        print(newSpeedDials)

        if force:
            print('Updates will apply automatically without confirmation')
        else:
            print('Updates will require confirmation before applying')
    
        cancel = False

        for phone in newSpeedDials:
            speedDials = {'speeddial': newSpeedDials[phone]['speedDials']}
            if force:
                self.updatePhoneSpeedDial( phone, speedDials)
            else:
                description = newSpeedDials[phone]['description']
                print(f'About to update Speed Dials on Phone:\n{description}')
                print(newSpeedDials[phone]['summary'])
                # print(speedDials)
                while True:
                    response = input(f'Enter [ Y / Yes ] to continue, [ N / No ] to Skip this phone or [C / Cancel] to Cancel \n')
                    
                    if response.upper() in ["Y", "YES"]:
                        print(speedDials)
                        self.updatePhoneSpeedDial( phone, speedDials)
                        break
                    elif response.upper() in ["N", "NO"]:
                        print(f'Skipping Speed Dial update for Phone {phone} ')
                        break
                    elif response.upper() in ["C", "Cancel"]:
                        print('Cancelling Speed Dial Updates')
                        cancel = True
                        break
                    else:
                        print('Invalid Response')
            
            if cancel:
                break

    def restoreSpeedDials(self, newSpeedDials, force=True):
        print(newSpeedDials)

        if force:
            print('Speed Dial restore will apply automatically without confirmation')
        else:
            print('Speed Dial restore will require confirmation before applying')
    
        cancel = False

        for phone in newSpeedDials:
            speedDials = {'speeddial': newSpeedDials[phone]['speedDials']}
            if force:
                self.updatePhoneSpeedDial( phone, speedDials)
            else:
                description = newSpeedDials[phone]['description']
                print(f'About to restore Speed Dials on Phone: {description}')
                print(self.restoreSummary(speedDials['speeddial']))
                while True:
                    response = input(f'Enter [ Y / Yes ] to continue, [ N / No ] to Skip this phone or [C / Cancel] to Cancel \n')
                
                    if response.upper() in ["Y", "YES"]:
                        print(speedDials)
                        self.updatePhoneSpeedDial( phone,  speedDials)
                        break
                    elif response.upper() in ["N", "NO"]:
                        print(f'Skipping Speed Dial update for Phone {phone} ')
                        break
                    elif response.upper() in ["C", "Cancel"]:
                        print('Cancelling Speed Dial Updates')
                        cancel = True
                        break
                    else:
                        print('Invalid Response')
            
            if cancel:
                break

    def restoreSummary(self, speedDials):
        print('creating summary')
        print(speedDials)
        summary = PrettyTable(['Number', 'Label'])
        for speedDial in speedDials:
            summary.add_row([speedDial['dirn'], speedDial['label']])
        return summary

