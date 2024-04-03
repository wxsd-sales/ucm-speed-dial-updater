from datetime import datetime
import pickle

from prettytable import PrettyTable

def saveBackup( location, filename, data):
    print('Backup Data Saved:')
    # print(data)
    timestamp = str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    with open(f'{location}/{filename}-{timestamp}.pk1', 'wb') as f:
        pickle.dump(data, f)
    return

def loadBackup(filename):
    with open(filename, 'rb') as f:
        backup = pickle.load(f)
    print('Backup Data loaded:')
    print(backup)
    return backup

def saveSurvey(location, filename, data):
    timestamp = str(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    with open(f'{location}/{filename}-{timestamp}.pk1', 'wb') as f:
        pickle.dump(data, f)
    return


def identifyUpdates(speedDials, directoryNumbers, min, max, replacement):
    updatedSpeedDials = {}
    for phone in speedDials:

        requiresUpdate = False
        speedDialsCopy = speedDials[phone].copy()
        summary = PrettyTable(['Number', 'Current Label', 'New Label'])

        for index, speedDial in enumerate(speedDials[phone]['speedDials']):
            speedDialLength = len(speedDial['dirn'])
            # If Directory number is too small or two lager, do not update
            if speedDialLength < min or speedDialLength > max:
                continue
            
            if speedDial['dirn'] in directoryNumbers and speedDial['label'] != directoryNumbers[speedDial['dirn']]:
                summary.add_row([speedDial['dirn'], speedDial['label'], directoryNumbers[speedDial['dirn']]])
                speedDialsCopy['speedDials'][index]['label'] =  directoryNumbers[speedDial['dirn']]
                requiresUpdate = True

            elif not speedDial['dirn'] in directoryNumbers and speedDial['label'] != replacement:
                summary.add_row([speedDial['dirn'], speedDial['label'], replacement])
                speedDialsCopy['speedDials'][index]['label'] = replacement
                
                requiresUpdate = True

        if requiresUpdate:
            updatedSpeedDials[phone] = speedDialsCopy
            updatedSpeedDials[phone]['summary'] = summary

    return updatedSpeedDials
