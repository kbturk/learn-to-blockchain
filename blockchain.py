'''
Javascript terminal interactions \transaction\new [POST]:
var hdr = new Headers({ 'Content-Type': 'application/json'});
fetch('http://127.0.0.1:5000/transactions/new', {method: 'POST', body: '{"sender": "bob", "recipient": "sally", "amount": 5000}', headers: hdr}).then(resp => console.log(resp))

for seeing the entire chain:
127.0.0.1:5000/chain

for mining:
127.0.0.1:5000/mine
'''

import hashlib
import json
from time import time
from uuid import uuid4
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, request

class Blockchain(object):
    def __init__(self): #in rust this would be a method
        self.chain = []
        self.current_transactions = []
    
        #time to create that genesis block
        self.new_block(previous_hash='1', proof=100)
        
    def new_block(self, proof, previous_hash):
        # creates a new block and adds it to the chain
        block = {
            'index': len(self.chain) +1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash':previous_hash or self.hash(self.chain[-1]),
        }
        
        #reset the current list of transactions
        self.current_transactions = []
        
        self.chain.append(block)
        return block
        
    def new_transaction(self, sender, recipient, amount):
        '''Creates a new transaction to go into the next mined block. 
        :return: <int> the index of the block that will hold this transaction.
        '''
        
        self.current_transactions.append({
            'sender':sender,
            'recipient':recipient,
            'amount':amount,
        })
        
        return self.last_block['index']+1
    
    @staticmethod 
    def hash(block):
        #Create an ordered dictionary
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    @property
    def last_block(self):
        #returns the last Block in the chain
        return self.chain[-1]
    

    def proof_of_work(self, last_proof):
        #Simple PoW algorithm: find p such that the hash contains at least 4 zeroes where p is the prevous p.
        #:param last_proof: <int>, :return: <int>
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof +=1
        return proof            
    
    @staticmethod
    def valid_proof(last_proof,proof):
        #does the hash contain at least 4 leading zeroes?
        
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] =="0000"
        
#Instantiate our Node:
app = Flask(__name__)

#Generate a globally unique address for this node.
node_identifier = str(uuid4()).replace('-','')

#Instantiate the blockchain
blockchain = Blockchain()

@app.route('/mine', methods= ['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    
    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1    
    )

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message':'new block forged',
        'index':block['index'],
        'transactions':block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    
    return jsonify(response),200

@app.route('/transactions/new', methods=['POST'])    
def new_transaction():
    values = request.get_json()
   
    #check that the requied fields are in the POSTed data:
    required = ['sender','recipient','amount']
    if not all(k in values for k in required):
       return 'Missing values', 400
       
    #create a new transaction.
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201
    
@app.route('/chain',methods=["GET"])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200
    
if __name__ == '__main__':
    app.run(host = '0.0.0.0',port=5000)