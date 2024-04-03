# UCM Speed Dial Updater

This is a example script which update the names of speed dials based on provisioning status for UCM Registered IP Phones

## Overview

Using the UCM AXL APIs, this script will identify any IP Phones with speed dials already configured and then will update the name of the speed dial with the username associated with that speed dial extension.

If the extension hasn't been provisioned to a user yet, the speed dial name will be renamed to a unavailable status. The wording of which is configurable within the script.

<img width="620" alt="image" src="https://github.com/wxsd-sales/ucm-speed-dial-updater/assets/21026209/a2159bcd-ce13-49fc-978d-29b7f141c957">



### Flow Diagram

![ucm-speed-dial-updater-flow](https://github.com/wxsd-sales/ucm-speed-dial-updater/assets/21026209/8f5e78fb-72c0-4c94-a9d4-cfdeedb697cb)


## Setup

### Prerequisites & Dependencies: 

- CUCM 12.5 or above
- CUCM Application Account with AXL Access
- Python version >= 3.10
- Pip install modules


<!-- GETTING STARTED -->

### Installation Steps:
1.  Close this repo:
    ```sh
    git clone https://github.com/wxsd-sales/ucm-speed-dial-updater.git
    ```
2.  Insert project requirements:
    ```sh
    pip install -r requirements.txt
    ```
3. Rename ``.env.example`` to ``.env`` and add your CUCM Server address and AXL Account Credentials:
    ```
    CUCM_ADDRESS=cucm.example.com
    AXL_USERNAME=axlaccount
    AXL_PASSWORD=axlaccountpassword
    ```
4. Run the script using:
    ```sh
    python speed_dial_updater.py
    ```
5. (Option) Setup a Cron job ( Linux ), Automator Task ( Mac)  or Scheduled Task ( Windows ) to periodically run this script and keep Speed Dial Labels updated on the CUCM
    
    
    
## Demo

<!-- Keep the following statement -->
*For more demos & PoCs like this, check out our [Webex Labs site](https://collabtoolbox.cisco.com/webex-labs).


## License

All contents are licensed under the MIT license. Please see [license](LICENSE) for details.


## Disclaimer

Everything included is for demo and Proof of Concept purposes only. Use of the site is solely at your own risk. This site may contain links to third party content, which we do not warrant, endorse, or assume liability for. These demos are for Cisco Webex usecases, but are not Official Cisco Webex Branded demos.


## Questions
Please contact the WXSD team at [wxsd@external.cisco.com](mailto:wxsd@external.cisco.com?subject=ucm-speed-dial-updater) for questions. Or, if you're a Cisco internal employee, reach out to us on the Webex App via our bot (globalexpert@webex.bot). In the "Engagement Type" field, choose the "API/SDK Proof of Concept Integration Development" option to make sure you reach our team. 
