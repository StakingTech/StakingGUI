# StakingGUI
Automatically manage UTXO sizes and improve staking rewards. Run in the background alongside your wallet(s) to create as many UTXOs of the desired size as neccisary, and to automaticaly create new UTXOs from incomming stakes. 

Install prerequisites:
sudo apt install python3
sudo apt install python3-pip
pip install setuptools --user
pip install -r requirements.txt

Running GUI:
python3 ./start_GUI.py

How do you use the Stake Helper App?
    Start the UTXO management GUI
    Enter the relevant details for your coin as shown in our Guide
    Enter the application path for the wallet as shown Here
    Hit the save button to store the details
    (Optional) add a new entry for each additional coin you would like to manage
    (Optional) Start the wallet
    (Optional) Save all values as the new defaults, or to a file
    Hit Start. Stake Helper will now monitor each wallet at the given interval to make sure that all of your UTXO are the specified size.
