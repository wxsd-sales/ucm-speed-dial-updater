import argparse


def _parse_arguments():
    parser = argparse.ArgumentParser(prog='UCM_Updater', 
                                 description='This Script updates the Speed Dials labels for IP Phones on your UCM Cluster by matching the Speed Dial with an Extension number')

    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_survey = subparsers.add_parser('survey', help='Identify mislabeled Speed Dials and genearte a report')

    parser_survey.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
                        help='Show debug logs')

    parser_survey.add_argument('--debug-soap', dest='soapDebug', action='store_true', default=False,    
                        help='Show SOAP Debug Logs')

    parser_survey.add_argument('--min-digits', dest='minDigits', action='store_const', const=4, default=4,
                        help='Minimum number of Speed Dial Digits which will be updated (default: 4)')

    parser_survey.add_argument('--max-digits', dest='maxDigits', action='store_const', const=4, default=4,
                        help='Maximum number of Speed Dial Digits which will be updated (default: 4)')

    parser_survey.add_argument('--replacement-token', dest='replacementToken', action='store_const', const='N/A', default='N/A',
                        help='Text to replace unfound Speed Dial Extensions (default: \'N/A\')')

    parser_update = subparsers.add_parser('update', help='Identify mislabeled Speed Dials and update them')

    parser_update.add_argument('-f','--force', dest='forceUpdate', action='store_true',
                        help='Perform Speed Dial updates without confirmation prompt')
    
    parser_update.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
                        help='Show debug logs')
    
    parser_update.add_argument('--debug-soap', dest='soapDebug', action='store_true', default=False,
                        help='Show SOAP Debug Logs')

    parser_update.add_argument('--min-digits', dest='minDigits',  default=4, type=int,
                        help='Minimum number of Speed Dial Digits which will be updated (default: 4)')
    parser_update.add_argument('--max-digits', dest='maxDigits',  default=4, type=int,
                        help='Maximum number of Speed Dial Digits which will be updated (default: 4)')

    parser_update.add_argument('--replacement-token', dest='replacementToken', action='store_const', const='N/A', default='N/A',
                        help='Text to replace unfound Speed Dial Extensions (default: \'N/A\')')

    parser_restore = subparsers.add_parser('restore', help='Restore Speed Dials from Backup')

    parser_restore.add_argument(dest='filename',  type=argparse.FileType('r'), help='Speed Dials Backup Filename')

    #parser_restoreFile = filesubparsers.add_argument('filename', type=argparse.FileType('r'), help='Speed Dials Backup Filename')

    #parser_restoreFile.add_argument('filename', dest='forceUpdate', action='store_true',
    #                    help='Perform Speed Dial restore without confirmation prompt')

    parser_restore.add_argument('-f', '--force', dest='forceUpdate', action='store_true',
                        help='Perform Speed Dial restore without confirmation prompt')
    
    parser_restore.add_argument('-d', '--debug', dest='debug', action='store_true', default=False,
                        help='Show debug logs')
    
    parser_restore.add_argument('--debug-soap', dest='soapDebug', action='store_true', default=False,
                        help='Show SOAP Debug Logs')

    # parser.add_argument('--ucm-address', dest='ucmAddress', action='store',
    #                     help='FQDN or IP Address of your UCM')

    # parser.add_argument('--axl-username', dest='axlUsername', action='store',
    #                     help='Username of your UCM AXL Account')

    # parser.add_argument('--axl-password', dest='axlPassword', action='store',
    #                     help='Password of your UCM AXL Account')

    return parser.parse_args()

CONSOLE_ARGS =  _parse_arguments()

# optional: delete function after use to prevent calling from other place
del _parse_arguments

