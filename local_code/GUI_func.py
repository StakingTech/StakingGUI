
def RPC_dict(form):
  RPC = {
    'coin_name': form._coin_name.value,
    'transaction_fee': form._transaction_fee,
    'port': form._RPC_port.value,
    'user': form._RPC_user.value,
    'pw': form._RPC_pw.value,
    'UTXO_size': form._UTXO_Size.value,
    'min_conf': form._min_conf.value,
    'max_conf': form._max_conf.value,
    'wallet_path': form._wallet_path.value}
  return RPC

def Saved_RPC_to_dicts(form):
    saved_RPC = form._save_RPC.value
    output_list = []
    for coin in saved_RPC:
        RPC = {
            'coin_name': coin[0],
            'port': coin[1],
            'user': coin[2],
            'pw': coin[3],
            'UTXO_size': coin[4],
            'min_conf': coin[5],
            'max_conf': coin[6],
            'wallet_path': coin[7],
            'transaction_fee': coin[8]}
        output_list.append(RPC)
    return output_list

def RPC_values_list(form):
	data = [form._coin_name.value,
		    form._RPC_port.value,
			form._RPC_user.value,
			form._RPC_pw.value,
			form._UTXO_Size.value,
			form._min_conf.value,
			form._max_conf.value,
			form._wallet_path.value,
            form._transaction_fee.value]
	return data

def populate_rpc(form, RPC_data):
    form._coin_name.value = RPC_data[0]
    form._RPC_port.value = RPC_data[1]
    form._RPC_user.value = RPC_data[2]
    form._RPC_pw.value = RPC_data[3]
    form._UTXO_Size.value = RPC_data[4]
    form._min_conf.value = RPC_data[5]
    form._max_conf.value = RPC_data[6]
    form._wallet_path.value = RPC_data[7]
    form._transaction_fee.value = RPC_data[8]

def fill_RPC(form, RPC_info):
    form._coin_name.value = RPC_info['coin_name']
    form._RPC_port.value = RPC_info['port']
    form._RPC_user.value = RPC_info['user']
    form._RPC_pw.value = RPC_info['pw']
    form._UTXO_Size.value = RPC_info['UTXO_size']
    form._min_conf.value = RPC_info['min_conf']
    form._max_conf.value = RPC_info['max_conf']
    form._wallet_path.value = RPC_info['wallet_path']
    form._transaction_fee.value = RPC_info['transaction_fee']
