import bpy
from bpy.props import EnumProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

import topologic
import time
try:
	from web3 import Web3, HTTPProvider
except:
	raise Exception("Error: Could not import web3.")

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def repeat(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
			# print(base,y)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def interlace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in interlace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList

def processItem(item, data):
    contract_address, contract_abi, wallet_address, wallet_private_key, infura_url = item

    w3 = Web3(HTTPProvider(infura_url))

    smartContract = w3.eth.contract(address=contract_address, abi=contract_abi)

    receipts = []

    #the next function calls mints the NFT
    nonce = w3.eth.get_transaction_count(wallet_address)
    tx_dict = smartContract.functions.setMaterialID(data[0], data[1], data[2]).buildTransaction({
        'chainId' : 4,
        'gas' : 2100000,  #some of this was throwing errors, double check gas amounts.
        'gasPrice' : w3.toWei('50', 'gwei'),
        'nonce' : nonce,
    })



    signed_tx = w3.eth.account.sign_transaction(tx_dict, wallet_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash, timeout=120, poll_latency=0.1)
    receipts.append(tx_receipt)



    outputList = []
    for tx_receipt in receipts:
        receipt = []
        receipt.append('blockHash: '+str(tx_receipt['blockHash']))
        receipt.append('blockNumber: '+str(tx_receipt['blockNumber']))
        receipt.append('contractAddress: '+str(tx_receipt['contractAddress']))
        receipt.append('cumulativeGasUsed: '+str(tx_receipt['cumulativeGasUsed']))
        receipt.append('from: '+str(tx_receipt['from']))
        receipt.append('gasUsed: '+str(tx_receipt['gasUsed']))
        receipt.append('logs: '+str(tx_receipt['logs']))
        receipt.append('to: '+str(tx_receipt['to']))
        receipt.append('transactionHash: '+str(tx_receipt['transactionHash']))
        receipt.append('tansactionIndex: '+str(tx_receipt['transactionIndex']))
        outputList.append(receipt)



    return outputList

replication = [("Trim", "Trim", "", 1),("Iterate", "Iterate", "", 2),("Repeat", "Repeat", "", 3),("Interlace", "Interlace", "", 4)]

class SvContractByParameters(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Contract from the input parameters   
	"""
	bl_idname = 'SvContractByParameters'
	bl_label = 'Contract.ByParameters'
	X: FloatProperty(name="X", default=0, precision=4, update=updateNode)
	Y: FloatProperty(name="Y",  default=0, precision=4, update=updateNode)
	Z: FloatProperty(name="Z",  default=0, precision=4, update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Iterate", items=replication, update=updateNode)

	def sv_init(self, context):
		#self.inputs[0].label = 'Auto'
		self.inputs.new('SvStringsSocket', 'contract_address')
		self.inputs.new('SvStringsSocket', 'contract_abi')
		self.inputs.new('SvStringsSocket', 'wallet_address')
		self.inputs.new('SvStringsSocket', 'private_key')
		self.inputs.new('SvStringsSocket', 'infura_node')
		self.inputs.new('SvStringsSocket', 'data')
		self.outputs.new('SvStringsSocket', 'Output')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		contractList = self.inputs['contract_address'].sv_get(deepcopy=True)
		abiList = self.inputs['contract_abi'].sv_get(deepcopy=True)
		walletList = self.inputs['wallet_address'].sv_get(deepcopy=True)
		keyList = self.inputs['private_key'].sv_get(deepcopy=True)
		infuraList = self.inputs['infura_node'].sv_get(deepcopy=True)
		dataList = self.inputs['data'].sv_get(deepcopy=True)
		contractList = flatten(contractList)
		abiList = flatten(abiList)
		walletList = flatten(walletList)
		keyList = flatten(keyList)
		infuraList = flatten(infuraList)
		inputs = [contractList, abiList, walletList, keyList, infuraList]
		if ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput, dataList))
		self.outputs['Output'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvContractByParameters)

def unregister():
    bpy.utils.unregister_class(SvContractByParameters)
