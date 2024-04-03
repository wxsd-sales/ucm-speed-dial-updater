import sys
import logging
import os
from prettytable import PrettyTable
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from ucm_connection import UCMConnection
from utils import identifyUpdates, loadBackup, saveBackup
from console_args import CONSOLE_ARGS

# Load CLI Argument
args = CONSOLE_ARGS

# Load .env file
load_dotenv()

# Enable Debugging if Debug parameter set
DEBUG = args.debug
SOAP_DEBUG = args.soapDebug


if DEBUG:
    print(args)


# Specify location of WSDL file and appliaction directories
WSDL_FILE = 'schema/AXLAPI.wsdl'
BACKUP_DIR = 'backups'
SURVEY_DIR = 'surveys'
LOG_DIR = 'logs'

# Load UCM Address, AXL Credentials and Variables from .env file or CLI arguments
UCM_ADDRESS = os.getenv( "UCM_ADDRESS" ) or args.ucmAddress
AXL_USERNAME = os.getenv( 'AXL_USERNAME' ) or args.axlUsername
AXL_PASSWORD = os.getenv( 'AXL_PASSWORD' ) or args.axlPassword
SPEED_DIAL_REPLACEMENT = 'N/A'


   

# Load MIN and MAX Digits from CLI or .env but default to 4 if none are found
MAX_DIGITS = 4
MIN_DIGITS = 4

if args.command != 'restore':
    SPEED_DIAL_REPLACEMENT = os.getenv( "REPLACEMENT_TOKEN" ) or args.replacementToken
    
    if os.getenv( 'MIN_DIGITS' ):
        MIN_DIGITS = int(os.getenv( 'MIN_DIGITS' ))
    else:
        MIN_DIGITS = args.minDigits

    if os.getenv( 'MAX_DIGITS' ):
        MAX_DIGITS = int(os.getenv( 'MAX_DIGITS' ))
    else:
        MAX_DIGITS = args.maxDigits




# Ensure UCM Address and AXL Credentails are not mssing before continuing
if UCM_ADDRESS is None:
    sys.exit('Error: Missing UCM Address in .env or argument')

if AXL_USERNAME is None:
    sys.exit('Error: Missing AXL Username in .env or argument')

if AXL_PASSWORD is None:
    sys.exit('Error: Missing AXL Password in .env or argument')

if MIN_DIGITS < 1 :
    sys.exit('Error: MIN Digits below 1')

if MIN_DIGITS > MAX_DIGITS:
    sys.exit('Error: MIN Digits is greater than MAX Digits')


# Create Bacup, Survey and Logging directories if not present
Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
Path(SURVEY_DIR).mkdir(parents=True, exist_ok=True)
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

timestamp = str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

logging.basicConfig(filename=LOG_DIR+'/log-'+timestamp+'.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

if DEBUG:
    print(f'Using UCM Address: {UCM_ADDRESS} - AXL Username:  {AXL_PASSWORD} - AXL PASSWORD: {"#" * len(AXL_PASSWORD) }')

print('Setting up Connection to UCM:', UCM_ADDRESS)

# Initilize UCM Connnection
connection = UCMConnection(UCM_ADDRESS, AXL_USERNAME, AXL_PASSWORD, WSDL_FILE, DEBUG, args.soapDebug )


match args.command:
    case "survey":
        print("Performing Speed Dial Survey")

        # Get list of Directory Number
        directoryNumbers = connection.getDirectoryNumbers()

        # Get list of phones enad ther speed dials
        phonesWithSpeedDials = connection.getAllPhonesWithSpeedDials()

        numOfPhones = len(phonesWithSpeedDials)

        if(numOfPhones == 0):
            sys.exit( 'No Phones with Speed Dials found - Survey was not created' )
        else: 
            print('Number of Phones with Speed Dials found:', numOfPhones)
            # Identify any Speed Dials that need updating
            updatedSpeedDials = identifyUpdates(phonesWithSpeedDials, directoryNumbers, MIN_DIGITS, MAX_DIGITS, SPEED_DIAL_REPLACEMENT)
            print('Phones requiring updates:', len(updatedSpeedDials))
            # Generate Survey Report

        sys.exit( 'Speed Dial Survey Completed' )

    case "update":
        print("Performing Speed Dial Update")

        # Get list of Directory Number
        directoryNumbers = connection.getDirectoryNumbers()

        # Get list of phones enad ther speed dials
        phonesWithSpeedDials = connection.getAllPhonesWithSpeedDials()

        numOfPhones = len(phonesWithSpeedDials)

        if(numOfPhones == 0):
            sys.exit( 'No Phones with Speed Dials found - Update cancelled' )
        else: 
            print('Number of Phones with Speed Dials found:', numOfPhones)
            
            # Save Backup
            print('Creating Speed Dial Backup')
            saveBackup(BACKUP_DIR, 'speeddial-backup', phonesWithSpeedDials)
            
            # Identify any Speed Dials that need updating
            updatedSpeedDials = identifyUpdates(phonesWithSpeedDials, directoryNumbers, MIN_DIGITS, MAX_DIGITS, SPEED_DIAL_REPLACEMENT)
            
            numOfPhonesRequiringUpdate = len(updatedSpeedDials)

            # If there are Speed Dials requiring updates and we are in update or force update mode, begin updating
            if numOfPhonesRequiringUpdate > 0 :
                print('Number of Phones requiring Speed Dial Updates:', numOfPhonesRequiringUpdate)

                connection.updateSpeedDials(updatedSpeedDials, args.forceUpdate)
            else:
                print('Update requested however there are no Speed Dials to update')

            # Generate Survey Report
            sys.exit( 'Speed Dial Update Completed' )

    case "restore":
        print("Performing Restore")
        filetest = args.filename
        print("Loading Backup File:", filetest.name)
        backup = loadBackup(filetest.name)
        if len(backup) > 0:
            print('Backup Loaded -', len(backup), 'Phones' if len(backup) > 1 else 'Phone' , ' found to restore')
            connection.restoreSpeedDials(backup, args.forceUpdate)
        else:
            sys.exit( 'Backup file loaded - No Backups Where Found' )
        sys.exit( 'Speed Dial Restore Completed' )
        
