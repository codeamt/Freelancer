"""
Web3 Integration

Flattened module containing Web3 client and service for blockchain interactions.
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from core.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import web3, but make it optional
try:
    from web3 import Web3
    from web3.middleware import geth_poa_middleware
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None
    Account = None


# ===== MODELS =====

@dataclass
class Web3Config:
    """Web3 configuration"""
    provider_url: str
    chain_id: int
    private_key: Optional[str] = None
    contract_address: Optional[str] = None
    abi: Optional[List[Dict[str, Any]]] = None
    gas_price: Optional[int] = None
    gas_limit: Optional[int] = None


@dataclass
class Wallet:
    """Web3 wallet"""
    address: str
    private_key: str
    public_key: Optional[str] = None
    balance: Optional[float] = None
    
    @classmethod
    def from_private_key(cls, private_key: str) -> 'Wallet':
        """Create wallet from private key"""
        if not WEB3_AVAILABLE:
            raise ImportError("Web3 library not available")
        
        account = Account.from_key(private_key)
        return cls(
            address=account.address,
            private_key=private_key,
            public_key=account.key.hex() if hasattr(account, 'key') else None
        )


@dataclass
class Transaction:
    """Web3 transaction"""
    hash: str
    from_address: str
    to_address: Optional[str]
    value: float
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    block_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    status: Optional[str] = None  # "pending", "confirmed", "failed"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """Create from transaction data"""
        timestamp = None
        if 'timestamp' in data:
            timestamp = datetime.fromtimestamp(data['timestamp'])
        
        return cls(
            hash=data.get('hash', ''),
            from_address=data.get('from', ''),
            to_address=data.get('to'),
            value=float(data.get('value', 0)),
            gas_used=data.get('gas_used'),
            gas_price=data.get('gas_price'),
            block_number=data.get('block_number'),
            timestamp=timestamp,
            status=data.get('status')
        )


@dataclass
class TokenInfo:
    """ERC20 token information"""
    address: str
    name: str
    symbol: str
    decimals: int
    total_supply: float
    balance: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenInfo':
        """Create from token data"""
        return cls(
            address=data.get('address', ''),
            name=data.get('name', ''),
            symbol=data.get('symbol', ''),
            decimals=data.get('decimals', 18),
            total_supply=float(data.get('total_supply', 0)),
            balance=data.get('balance')
        )


# ===== WEB3 CLIENT =====

class Web3Client:
    """Web3 client for blockchain interactions"""
    
    def __init__(self, config: Optional[Web3Config] = None):
        if not WEB3_AVAILABLE:
            raise ImportError("Web3 library not available. Install with: pip install web3")
        
        if config is None:
            config = Web3Config(
                provider_url=os.getenv("WEB3_PROVIDER_URL", "http://localhost:8545"),
                chain_id=int(os.getenv("WEB3_CHAIN_ID", "1")),
                private_key=os.getenv("WEB3_PRIVATE_KEY")
            )
        
        self.config = config
        self.w3 = Web3(Web3.HTTPProvider(config.provider_url))
        
        # Add POA middleware for testnets
        if config.chain_id not in [1, 5]:  # Not mainnet or goerli
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Set up account if private key provided
        self.account = None
        if config.private_key:
            self.account = Account.from_key(config.private_key)
        
        # Set up contract if ABI provided
        self.contract = None
        if config.contract_address and config.abi:
            self.contract = self.w3.eth.contract(
                address=config.contract_address,
                abi=config.abi
            )
        
        logger.info(f"Web3 client initialized for chain {config.chain_id}")
    
    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        return self.w3.is_connected()
    
    def get_block_number(self) -> int:
        """Get current block number"""
        return self.w3.eth.block_number
    
    def get_balance(self, address: str) -> float:
        """Get ETH balance for address"""
        try:
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return float(balance_eth)
        except Exception as e:
            logger.error(f"Failed to get balance for {address}: {e}")
            return 0.0
    
    def create_wallet(self) -> Wallet:
        """Create a new wallet"""
        account = Account.create()
        return Wallet(
            address=account.address,
            private_key=account.key.hex(),
            public_key=account.key.hex() if hasattr(account, 'key') else None
        )
    
    def send_eth(self, to_address: str, amount_eth: float, private_key: Optional[str] = None) -> Transaction:
        """Send ETH to another address"""
        try:
            # Use provided private key or config private key
            key = private_key or self.config.private_key
            if not key:
                raise ValueError("Private key required")
            
            account = Account.from_key(key)
            
            # Get nonce
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Build transaction
            tx = {
                'nonce': nonce,
                'to': to_address,
                'value': self.w3.to_wei(amount_eth, 'ether'),
                'gas': self.config.gas_limit or 21000,
                'gasPrice': self.config.gas_price or self.w3.eth.gas_price,
                'chainId': self.config.chain_id
            }
            
            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get transaction details
            tx_data = self.w3.eth.get_transaction(tx_hash)
            
            transaction = Transaction(
                hash=tx_hash.hex(),
                from_address=tx_data['from'],
                to_address=tx_data['to'],
                value=float(self.w3.from_wei(tx_data['value'], 'ether')),
                gas_used=receipt.gasUsed,
                gas_price=tx_data['gasPrice'],
                block_number=receipt.blockNumber,
                status="confirmed" if receipt.status == 1 else "failed"
            )
            
            logger.info(f"Sent {amount_eth} ETH to {to_address}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to send ETH: {e}")
            raise
    
    def get_transaction(self, tx_hash: str) -> Transaction:
        """Get transaction details"""
        try:
            tx_data = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            # Get block timestamp
            timestamp = None
            if receipt.blockNumber:
                block = self.w3.eth.get_block(receipt.blockNumber)
                timestamp = datetime.fromtimestamp(block.timestamp)
            
            transaction = Transaction(
                hash=tx_hash,
                from_address=tx_data['from'],
                to_address=tx_data['to'],
                value=float(self.w3.from_wei(tx_data['value'], 'ether')),
                gas_used=receipt.gasUsed,
                gas_price=tx_data['gasPrice'],
                block_number=receipt.blockNumber,
                timestamp=timestamp,
                status="confirmed" if receipt.status == 1 else "failed"
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to get transaction {tx_hash}: {e}")
            raise
    
    def get_token_info(self, token_address: str) -> TokenInfo:
        """Get ERC20 token information"""
        if not self.contract:
            raise ValueError("Contract not configured")
        
        try:
            # Standard ERC20 functions
            name = self.contract.functions.name().call()
            symbol = self.contract.functions.symbol().call()
            decimals = self.contract.functions.decimals().call()
            total_supply = self.contract.functions.totalSupply().call()
            
            token_info = TokenInfo(
                address=token_address,
                name=name,
                symbol=symbol,
                decimals=decimals,
                total_supply=float(total_supply / (10 ** decimals))
            )
            
            logger.info(f"Retrieved token info: {symbol}")
            return token_info
            
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            raise
    
    def get_token_balance(self, token_address: str, account_address: str) -> float:
        """Get ERC20 token balance"""
        if not self.contract:
            raise ValueError("Contract not configured")
        
        try:
            balance = self.contract.functions.balanceOf(account_address).call()
            decimals = self.contract.functions.decimals().call()
            
            return float(balance / (10 ** decimals))
            
        except Exception as e:
            logger.error(f"Failed to get token balance: {e}")
            return 0.0
    
    def send_token(self, token_address: str, to_address: str, amount: float, private_key: Optional[str] = None) -> Transaction:
        """Send ERC20 tokens"""
        if not self.contract:
            raise ValueError("Contract not configured")
        
        try:
            # Use provided private key or config private key
            key = private_key or self.config.private_key
            if not key:
                raise ValueError("Private key required")
            
            account = Account.from_key(key)
            
            # Get decimals
            decimals = self.contract.functions.decimals().call()
            amount_raw = int(amount * (10 ** decimals))
            
            # Build transaction
            tx_data = self.contract.functions.transfer(to_address, amount_raw).build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': self.config.gas_limit or 100000,
                'gasPrice': self.config.gas_price or self.w3.eth.gas_price,
                'chainId': self.config.chain_id
            })
            
            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx_data, key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get transaction details
            tx_details = self.w3.eth.get_transaction(tx_hash)
            
            transaction = Transaction(
                hash=tx_hash.hex(),
                from_address=tx_details['from'],
                to_address=tx_details['to'],
                value=float(self.w3.from_wei(tx_details['value'], 'ether')),
                gas_used=receipt.gasUsed,
                gas_price=tx_details['gasPrice'],
                block_number=receipt.blockNumber,
                status="confirmed" if receipt.status == 1 else "failed"
            )
            
            logger.info(f"Sent {amount} tokens to {to_address}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to send tokens: {e}")
            raise


# ===== WEB3 SERVICE =====

class Web3Service:
    """High-level Web3 service for common operations"""
    
    def __init__(self, config: Optional[Web3Config] = None):
        self.client = Web3Client(config)
    
    def create_wallet(self) -> Wallet:
        """Create a new wallet"""
        return self.client.create_wallet()
    
    def get_wallet_balance(self, address: str) -> float:
        """Get wallet balance"""
        return self.client.get_balance(address)
    
    def transfer_eth(self, from_private_key: str, to_address: str, amount_eth: float) -> Transaction:
        """Transfer ETH between wallets"""
        return self.client.send_eth(to_address, amount_eth, from_private_key)
    
    def get_transaction_status(self, tx_hash: str) -> Transaction:
        """Get transaction status"""
        return self.client.get_transaction(tx_hash)
    
    def get_token_balance(self, token_address: str, wallet_address: str) -> float:
        """Get token balance for wallet"""
        return self.client.get_token_balance(token_address, wallet_address)
    
    def transfer_token(self, token_address: str, from_private_key: str, to_address: str, amount: float) -> Transaction:
        """Transfer tokens between wallets"""
        return self.client.send_token(token_address, to_address, amount, from_private_key)
    
    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        return self.client.is_connected()
    
    def get_current_block(self) -> int:
        """Get current block number"""
        return self.client.get_block_number()


# Factory functions
def create_web3_client(config: Optional[Web3Config] = None) -> Web3Client:
    """Create a Web3 client instance"""
    return Web3Client(config)


def create_web3_service(config: Optional[Web3Config] = None) -> Web3Service:
    """Create a Web3 service instance"""
    return Web3Service(config)


# Convenience functions
def create_wallet() -> Wallet:
    """Convenience function to create a wallet"""
    client = Web3Client()
    try:
        return client.create_wallet()
    finally:
        client.w3.provider.disconnect()


def get_eth_balance(address: str) -> float:
    """Convenience function to get ETH balance"""
    client = Web3Client()
    try:
        return client.get_balance(address)
    finally:
        client.w3.provider.disconnect()


def send_eth(to_address: str, amount_eth: float, private_key: str) -> Transaction:
    """Convenience function to send ETH"""
    client = Web3Client()
    try:
        return client.send_eth(to_address, amount_eth, private_key)
    finally:
        client.w3.provider.disconnect()


__all__ = [
    # Models
    'Web3Config',
    'Wallet',
    'Transaction',
    'TokenInfo',
    
    # Client
    'Web3Client',
    
    # Service
    'Web3Service',
    
    # Factory
    'create_web3_client',
    'create_web3_service',
    
    # Convenience
    'create_wallet',
    'get_eth_balance',
    'send_eth',
]
