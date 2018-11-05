#!/usr/bin/python
from pyforms 			import BaseWidget
from pyforms.controls 	import ControlText
from pyforms.controls 	import ControlButton
from pyforms.controls 	import ControlTextArea
from pyforms.controls 	import ControlCombo
from pyforms.controls 	import ControlList
import pyforms
import AnyQt
from AnyQt.QtWidgets import QFileDialog
from AnyQt import QtCore
from AnyQt.QtCore import Qt, QObject, QCoreApplication, QThread, QSize
import json
import os.path
import subprocess
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import threading
import time
import local_code

#Import stylesheet
#PYFORMS_STYLESHEET = 'styles.css'

#Alpha Software, use at your own risk, no warranty express or implied
__author__      = "Staking Tech"
__credits__     = ["Staking_Tech"]
__version__     = "0.1"


class StakeScript(BaseWidget):
	timer = None
	RPC_threads = []
	
	# Test the wallet connection with a simple RPC getinfo command
	def __connect_buttonAction(self):
		RPC = local_code.GUI_func.RPC_dict(self)
		try:
			rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:%s"%(RPC['user'], RPC['pw'], RPC['port']))
			self._log.__add__(rpc_connection.getinfo())
		except Exception as e:
			self._log.__add__("Error: " + str(e))
			pass

	def __add_coin_buttonAction(self):
		new_RPC = self.default_RPC_data

		# Ensure the port generated hasn't been used already
		existing_RPC = self._save_RPC.value
		for row in existing_RPC:
			while new_RPC[1] == row[1]:
				new_RPC[1] = str(int(new_RPC[1]) + 1)

		# Ensure coin name doesn't already exist in list
		if [new_RPC[0]] in self._coin_list.value:
			while [new_RPC[0]] in self._coin_list.value:
				new_RPC[0] += '_'
		else:
			local_code.GUI_func.populate_rpc(self, self.default_RPC_data)

		self._coin_list.__add__([new_RPC[0]])
		self._save_RPC.__add__(new_RPC)
		self._coin_list.resize_rows_contents()

	def __remove_coin_buttonAction(self):
		selected_index = self._coin_list.selected_row_index
		multi_selection = self._coin_list.selected_rows_indexes

		if selected_index is None:
			return

		if len(multi_selection) > 1:
			multi_selection = reversed(multi_selection)
		else:
			multi_selection = [selected_index]
		for index in multi_selection:
			self._coin_list.__sub__(index)
			self._save_RPC.__sub__(index)
		self._coin_list.resize_rows_contents()

	def __save_coin_buttonAction(self):
		current_RPC = local_code.GUI_func.RPC_values_list(self)
		saved_RPC = self._save_RPC.value
		index = 0
		found_flag = False
		for row in saved_RPC:
			if current_RPC[0] == row[0]:
				found_flag = True
				col = 0
				for value in current_RPC:
					self._save_RPC.set_value(col, index, value)
					col += 1
				break
			index += 1
		if not found_flag:
			self._coin_list.__add__([current_RPC[0]])
			self._save_RPC.__add__(current_RPC)
		self._coin_list.resize_rows_contents()

	def __change_coin_selection(self):
		# Check if data changed and needs to be saved
		current_RPC = local_code.GUI_func.RPC_values_list(self)
		# Populate RPC fields with newly selected coin
		name = self._coin_list.get_currentrow_value()
		if not name:
			self._log.__add__("tried to populate, failed, name: {0}".format(name))
			return
		name = name[0]
		for row in self._save_RPC.value:
			if row[0] == name:
				local_code.GUI_func.populate_rpc(self, row)
				break

	def __lauch_wallet_buttonAction(self):
		RPC = local_code.GUI_func.RPC_dict(self)
		command = [ self._wallet_path.value,
					'-server',
					'-rpcuser={0}'.format(RPC['user']),
					'-rpcpassword={0}'.format(RPC['pw']),
					'-rpcport={0}'.format(RPC['port'])]
		subprocess.Popen(command)

	def write_to_log(self, text):
		self._log.__add__(text)
		self.timer = threading.Timer(5, self.write_to_log, ["timer 2"])
		self.timer.start()

	def start_timer(self):
		#TODO Space out the starting of new processes equally rather than all at once
		self.timer = threading.Timer(int(self._run_every.value) * 60, self.start_RPC_thread)
		self.timer.start()

	def __start_button_buttonAction(self):
		self._log.__add__("Starting: Will check wallets now and every {0} minutes.".format(self._run_every.value))
		self.start_timer()
		self.start_RPC_thread()

	def __stop_button_buttonAction(self):
		if self.timer:
			self.timer.cancel()
			self._log.__add__("Stopped monitoring wallets...")
			self.timer = None

	def start_RPC_thread(self):
		coin_list = local_code.GUI_func.Saved_RPC_to_dicts(self)
		for coin_data in coin_list:
			#TODO space threads spawn out, rather than starting them all at once
			self.RPC_threads.append(local_code.RPC_func.wallet_functions(coin_data))
			self.RPC_threads[-1].data_output.connect(self.on_data_ready)
			self.RPC_threads[-1].start()
		self.start_timer()

	def on_data_ready(self, data):
		if not data.endswith(":DEBUG"):
			#0 is only for debug information
			self._log.__add__("{0}".format(data))

	def __browse_buttonAction(self):
		filename, _ = QFileDialog.getOpenFileNames(self, 'Select file')
		self._wallet_path.value = filename[0]

	def __clear_log(self):
		self._log._form.plainTextEdit.setPlainText("")

	def __save_defaults(self):
		data = {}
		self.save_form(data)
		with open("defaults.dat", 'w') as output_file: json.dump(data, output_file)

	def __load(self):
		filename, _ = QFileDialog.getOpenFileNames(self, 'Select file')
		print (filename)
		if filename:
			self._coin_list.clear()
			self._save_RPC.clear()
			self.load_form_filename(str(filename[0]))
			self._coin_list.resize_rows_contents()

	def __init__(self):
		super(StakeScript,self).__init__('Stake Helper')
		self.set_margin(4)

		self._log = ControlTextArea()
		self._log.autoscroll = True
		self._log.readonly = True

		self._coin_name = ControlText('Coin Name')
		self._transaction_fee = ControlText('Transaction Fee')
		self._RPC_port =  ControlText('RPC Port')
		self._RPC_user 	= ControlText('RPC User')
		self._RPC_pw 		= ControlText('RPC Password')
		self._UTXO_Size 		= ControlText('UTXO Size')
		self._min_conf = ControlText('Minimum confirmations')
		self._max_conf = ControlText('Maximum confirmations')

		self._run_every = ControlText('Check Every')
		self._wallet_path = ControlText('Wallet Executable')
		self._browse_button = ControlButton("Browse")
		self._browse_button.value = self.__browse_buttonAction
		self._launch_wallet_button = ControlButton("Launch Wallet")
		self._launch_wallet_button.value = self.__lauch_wallet_buttonAction

		self.default_RPC_data = [
			"Coin Name", "8765", "Username", "Password", "100", "21", "1000", "", "0.00001"]
		local_code.GUI_func.populate_rpc(self, self.default_RPC_data)

		self._coin_list = ControlList()
		self._coin_list.readonly = True
		self._coin_list.autoscroll = True
		self._coin_list.item_selection_changed_event = self.__change_coin_selection
		self._coin_list.horizontal_headers = ["Coins"]

		#Hidden table used to store form field info for multiple coins
		self._save_RPC = ControlList()

		self._add_coin = ControlButton('Add')
		self._add_coin.value = self.__add_coin_buttonAction
		self._remove_coin = ControlButton('Del')
		self._remove_coin.value = self.__remove_coin_buttonAction
		self._save_coin = ControlButton('Save')
		self._save_coin.value = self.__save_coin_buttonAction

		self._connect_button 		= ControlButton('Test RPC Connection')
		self._connect_button.value = self.__connect_buttonAction

		self._clear_log_button = ControlButton('Clear Log')
		self._clear_log_button.value = self.__clear_log

		self._start_button = ControlButton('Start')
		self._start_button.value = self.__start_button_buttonAction
		self._stop_button = ControlButton('Stop')
		self._stop_button.value = self.__stop_button_buttonAction

 		# Determines the layout of the form fields
		self.formset = [
			('_coin_list',
		 		[('_coin_name','_transaction_fee','_UTXO_Size'),
				('_wallet_path', '_browse_button'),
				('_RPC_port','_RPC_user', '_RPC_pw'),
				('_min_conf', '_max_conf'),
				('_launch_wallet_button', '_connect_button'),
				]),
			('_add_coin', '_remove_coin', '_save_coin', ' ', "_clear_log_button"),
			'=',
			"Run Log: ", '_log', (' ', '_run_every', ' Minutes', ' ', "_start_button", "_stop_button", ' ')]

		# Define the top menu options
		self.mainmenu = [
	        { 'Save': [
	            {'To file...': self.save_window},
				{'Set current as Default': self.__save_defaults}
				]
			},
			{ 'Load': [{'From file...': self.__load},]
	        },
			{ 'Tools': [{'Clear Log': self.__clear_log}]}
			]

		# Load the default values
		if os.path.exists("defaults.dat"):
			self.load_form_filename("defaults.dat")
		else:
			self.__add_coin_buttonAction()

##################################################################################################################
#Execute the application
if __name__ == "__main__": pyforms.start_app( StakeScript, geometry=(50, 50, 700, 700) )

#self._log.__add__("MOOEJGOIEHGO") #Prints after form closes
