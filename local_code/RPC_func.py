import argparse
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import logging
from decimal import *
import math
import datetime

import AnyQt
from AnyQt import QtCore
from AnyQt.QtCore import Qt, QObject, QCoreApplication, QThread, QSize

def get_permission():
    #TODO impliment popup for permission
    pass

class wallet_functions(QtCore.QThread):
    data_output = QtCore.pyqtSignal(object)
    def __init__(self, coin_list):
        QtCore.QThread.__init__(self)
        self.coin_list = coin_list
    def run(self):
        LOG_PATH = 'RPC.log'
        logging.basicConfig(filename=LOG_PATH, level=logging.INFO)
        log = logging.getLogger(__name__)

        output = self.check_for_stake(self.coin_list, log)
        self.data_output.emit('{0}: {1}'.format(self.coin_list['coin_name'], output))


    def check_for_stake(self, RPC, log):
        try:
            rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:%s"%(RPC['user'], RPC['pw'], RPC['port']))
            # Check integrity of wallet before getting wallet info
            check_wallet = rpc_connection.checkwallet()
        except:
            return "Unable to connect to wallet. Verify that it's running and your RPC settings are correct"

        if 'wallet check passed' not in check_wallet:
            log.info(check_wallet)
            rpc_connection.repairwallet()
            log.info("**Wallet was repaired**")

        try:
            txs = rpc_connection.listunspent(int(RPC['min_conf']), int(RPC['max_conf'])) # Only work with inputs that aren't mature
        except:
            return "Unable to run 'listunspent' over RPC, check that the wallet is still running"
        input_sum = 0
        utxo_size = Decimal(RPC['UTXO_size'])
        input_tx = []
        addresses_to_reuse = []
        for each_tx in txs:
            # Check out each existing transaction for desired size, sum up inputs that aren't
            if each_tx['amount'] != utxo_size:
                input_sum += each_tx['amount']
                input_tx.append({"txid":each_tx['txid'],"vout":each_tx['vout']})
                if 'account' in each_tx and each_tx['account'] == 'stake_script' and each_tx['address'] not in addresses_to_reuse:
                    # reuse input addresses for a new output if they have the label 'stake_script'
                    addresses_to_reuse.append(each_tx['address'])

        if input_sum < utxo_size:
            log.debug("DEBUG: Total coins: {0} is not enough to make a new packet of {1}".format(input_sum, utxo_size))
            return "Total coins: {0} is not enough to make a new packet of {1} :DEBUG".format(input_sum, utxo_size)

        # Reuse or make a new change and stake addresses
        change_address = rpc_connection.getaddressesbyaccount("change")
        if len(change_address) == 0:
            change_address = [rpc_connection.getnewaddress("change")]
        stake_addresses = rpc_connection.getaddressesbyaccount("stake_script")
        for addr in stake_addresses:
            amount = rpc_connection.getreceivedbyaddress(addr)
            if amount == 0 and addr not in addresses_to_reuse:
                # Only reuse addresses with the label stake_script and zero balance for safety
                addresses_to_reuse.append(addr)

        output_addresses = {}
        number_of_splits = int(input_sum / utxo_size)
        if len(addresses_to_reuse) < number_of_splits:
            # Make as many new addresses as needed to split inputs into 'size' outputs
            num_to_make = number_of_splits - len(addresses_to_reuse)
            #if not arg.noconfirm:
                # TODO implement
            #    print("About to make {0} new stake address(es), confirm".format(num_to_make))
            #    get_permission()
            for _ in range(num_to_make):
                addresses_to_reuse.append(rpc_connection.getnewaddress('stake_script'))

        for _ in range(number_of_splits):
            output_addresses[addresses_to_reuse.pop()] = utxo_size

        #print(output_addresses)
        assert(int(input_sum / utxo_size) == len(output_addresses)), "Not enough output addresses for number of UTXO splits!"

        number_of_splits = len(output_addresses)
        numbytes = 181 * len(input_tx) + 34* (number_of_splits+1) + 10
        numKB = math.ceil(numbytes / 1000)
        TX_FEE = Decimal(RPC['transaction_fee']) * numKB
        log.debug("transaction fee is %d : %d bytes, fee multiple is %d"%(TX_FEE, numbytes,numKB))

        change_amount = input_sum - (utxo_size * number_of_splits) - TX_FEE
        output_addresses[change_address[0]] = change_amount
        assert (change_amount > 0), "Change amount cannot be less than zero"
        assert(change_amount + TX_FEE + (utxo_size*number_of_splits) == input_sum), "Coins will be lost if the total output != input"

        log.debug("{0} Inputs {1}".format(len(input_tx),input_tx))
        log.debug("{0} Outputs {1}".format(len(output_addresses), output_addresses))
        log.info("{0} (Input total) = {2} ({1}_UTXO packets) + {3} (change) + {4} (fee)".format(input_sum,number_of_splits,utxo_size*number_of_splits,change_amount, TX_FEE))

        # Generate, sign, and send the raw transaction
        raw_tx = rpc_connection.createrawtransaction(input_tx, output_addresses)
        signed_tx = rpc_connection.signrawtransaction(raw_tx)
        if not signed_tx['complete']:
            log.error("Signing failed of raw tranaction: {0}\nInputs: {1}\nOutputs: {2}".format(raw_tx, input_tx, output_addresses))
            return "Signing of raw transaction did not complete successfully, make sure wallet is functioning properly"

        #if not arg.noconfirm:
        #    print("About to send transaction, confirm")
        #    get_permission()

        log.info("Attempting to send: {0} (Total inputs) = {2} ({1} new UTXO) + {3} (change) + {4} (fee)".format(input_sum,number_of_splits,utxo_size*number_of_splits,change_amount, TX_FEE))
        try:
            sent = rpc_connection.sendrawtransaction(signed_tx['hex'])
        except Exception as e:
            return "Sending transaction failed (Your wallet might need more time to update): {0}".format(str(e))
        log.info("TX successful: transaction ID: {0}".format(sent))
        now = datetime.datetime.now().strftime("%m-%d %H:%M")
        return "{6} TX {5} successful: {0} (Total inputs) = {2} ({1} new UTXO) + {3} (change) + {4} (fee)".format(input_sum,number_of_splits,utxo_size*number_of_splits,change_amount, TX_FEE, sent, now)
