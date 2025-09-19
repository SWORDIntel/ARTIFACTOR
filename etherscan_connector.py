#!/usr/bin/env python3
"""
Etherscan API Connector for Claude.ai
Provides easy access to Ethereum blockchain data via Etherscan API
"""

import requests
import json
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import time

@dataclass
class EtherscanConfig:
    """Configuration for Etherscan API connector"""
    api_key: str = "SHNQ2KS7N6D8B175GYUSJMESDKBZH7H8PS"
    base_url: str = "https://api.etherscan.io/api"
    timeout: int = 30
    rate_limit_delay: float = 0.2  # 5 requests per second limit

class EtherscanConnector:
    """Main connector class for Etherscan API"""

    def __init__(self, config: Optional[EtherscanConfig] = None):
        self.config = config or EtherscanConfig()
        self.session = requests.Session()

    def _make_request(self, params: Dict) -> Dict:
        """Make API request with rate limiting and error handling"""
        params['apikey'] = self.config.api_key

        try:
            time.sleep(self.config.rate_limit_delay)
            response = self.session.get(
                self.config.base_url,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            data = response.json()
            if data.get('status') == '0' and data.get('message') != 'No transactions found':
                raise Exception(f"API Error: {data.get('message')}")

            return data

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON decode error: {str(e)}")

    # Account APIs
    def get_eth_balance(self, address: str) -> float:
        """Get ETH balance for an address"""
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': 'latest'
        }
        result = self._make_request(params)
        return float(result['result']) / 10**18  # Convert from wei to ETH

    def get_token_balance(self, address: str, contract_address: str) -> float:
        """Get token balance for an address"""
        params = {
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': contract_address,
            'address': address,
            'tag': 'latest'
        }
        result = self._make_request(params)
        return float(result['result'])

    def get_transactions(self, address: str, start_block: int = 0, end_block: int = 99999999,
                        page: int = 1, offset: int = 10) -> List[Dict]:
        """Get transaction history for an address"""
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': start_block,
            'endblock': end_block,
            'page': page,
            'offset': offset,
            'sort': 'desc'
        }
        result = self._make_request(params)
        return result['result']

    def get_internal_transactions(self, address: str, start_block: int = 0,
                                 end_block: int = 99999999) -> List[Dict]:
        """Get internal transaction history for an address"""
        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'startblock': start_block,
            'endblock': end_block,
            'sort': 'desc'
        }
        result = self._make_request(params)
        return result['result']

    def get_token_transfers(self, address: str, contract_address: Optional[str] = None,
                           start_block: int = 0, end_block: int = 99999999) -> List[Dict]:
        """Get token transfer events for an address"""
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'startblock': start_block,
            'endblock': end_block,
            'sort': 'desc'
        }
        if contract_address:
            params['contractaddress'] = contract_address

        result = self._make_request(params)
        return result['result']

    # Contract APIs
    def get_contract_abi(self, contract_address: str) -> List[Dict]:
        """Get contract ABI"""
        params = {
            'module': 'contract',
            'action': 'getabi',
            'address': contract_address
        }
        result = self._make_request(params)
        return json.loads(result['result'])

    def get_contract_source_code(self, contract_address: str) -> Dict:
        """Get contract source code"""
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': contract_address
        }
        result = self._make_request(params)
        return result['result'][0] if result['result'] else {}

    # Transaction APIs
    def get_transaction_status(self, tx_hash: str) -> Dict:
        """Get transaction execution status"""
        params = {
            'module': 'transaction',
            'action': 'getstatus',
            'txhash': tx_hash
        }
        return self._make_request(params)

    def get_transaction_receipt(self, tx_hash: str) -> Dict:
        """Get transaction receipt status"""
        params = {
            'module': 'transaction',
            'action': 'gettxreceiptstatus',
            'txhash': tx_hash
        }
        return self._make_request(params)

    # Block APIs
    def get_block_reward(self, block_number: int) -> Dict:
        """Get block and uncle rewards"""
        params = {
            'module': 'block',
            'action': 'getblockreward',
            'blockno': block_number
        }
        return self._make_request(params)

    # Stats APIs
    def get_eth_supply(self) -> float:
        """Get total ETH supply"""
        params = {
            'module': 'stats',
            'action': 'ethsupply'
        }
        result = self._make_request(params)
        return float(result['result']) / 10**18

    def get_eth_price(self) -> Dict:
        """Get current ETH price in USD and BTC"""
        params = {
            'module': 'stats',
            'action': 'ethprice'
        }
        result = self._make_request(params)
        return {
            'usd': float(result['result']['ethusd']),
            'btc': float(result['result']['ethbtc'])
        }

    def get_gas_oracle(self) -> Dict:
        """Get gas price oracle"""
        params = {
            'module': 'gastracker',
            'action': 'gasoracle'
        }
        try:
            result = self._make_request(params)
            return {
                'safe_gas_price': int(result['result']['SafeGasPrice']),
                'standard_gas_price': int(result['result']['StandardGasPrice']),
                'fast_gas_price': int(result['result']['FastGasPrice']),
                'propose_gas_price': float(result['result']['ProposeGasPrice'])
            }
        except Exception as e:
            # Fallback gas prices if API fails
            return {
                'safe_gas_price': 20,
                'standard_gas_price': 25,
                'fast_gas_price': 30,
                'propose_gas_price': 25.0
            }

    # Utility methods
    def is_contract(self, address: str) -> bool:
        """Check if address is a contract"""
        try:
            source = self.get_contract_source_code(address)
            return bool(source.get('SourceCode'))
        except:
            return False

    def get_address_summary(self, address: str) -> Dict:
        """Get comprehensive address summary"""
        summary = {
            'address': address,
            'eth_balance': self.get_eth_balance(address),
            'is_contract': self.is_contract(address)
        }

        try:
            transactions = self.get_transactions(address, offset=5)
            summary['transaction_count'] = len(transactions)
            summary['latest_transactions'] = transactions[:3]
        except:
            summary['transaction_count'] = 0
            summary['latest_transactions'] = []

        return summary

def main():
    """Example usage of the Etherscan connector"""
    connector = EtherscanConnector()

    # Example Ethereum address (Vitalik's address)
    vitalik_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

    try:
        print("=== Etherscan API Connector Demo ===\n")

        # Get ETH balance
        balance = connector.get_eth_balance(vitalik_address)
        print(f"ETH Balance: {balance:.4f} ETH")

        # Get ETH price
        price = connector.get_eth_price()
        print(f"ETH Price: ${price['usd']:.2f} USD, {price['btc']:.6f} BTC")

        # Get gas prices
        gas = connector.get_gas_oracle()
        print(f"Gas Prices - Safe: {gas['safe_gas_price']} gwei, Standard: {gas['standard_gas_price']} gwei, Fast: {gas['fast_gas_price']} gwei")

        # Get recent transactions
        try:
            transactions = connector.get_transactions(vitalik_address, offset=3)
            print(f"\nRecent Transactions ({len(transactions)}):")
            for tx in transactions:
                value_eth = float(tx['value']) / 10**18
                print(f"  - Hash: {tx['hash'][:20]}... Value: {value_eth:.4f} ETH")
        except Exception as e:
            print(f"\nTransactions: Could not fetch (Rate limited or no data)")

        # Get address summary
        try:
            summary = connector.get_address_summary(vitalik_address)
            print(f"\nAddress Summary:")
            print(f"  - Address: {summary['address']}")
            print(f"  - Balance: {summary['eth_balance']:.4f} ETH")
            print(f"  - Is Contract: {summary['is_contract']}")
            print(f"  - Transaction Count: {summary['transaction_count']}")
        except Exception as e:
            print(f"\nAddress Summary: Could not generate (Rate limited)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()