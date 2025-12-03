"""
Web3 Service - Base class for blockchain interactions

Provides foundational Web3 functionality that can be extended by add-ons
for specific blockchain use cases (NFTs, DeFi, DAOs, etc.)
"""

from typing import Optional, Dict, Any, List
from core.utils.logger import get_logger
import os

logger = get_logger(__name__)


class Web3Service:
    """
    Base Web3 service for blockchain interactions
    
    Features:
    - Wallet connection and management
    - Smart contract interactions
    - Transaction handling
    - Event listening
    - Multi-chain support
    
    Usage:
        web3_service = Web3Service(provider_url="https://mainnet.infura.io/v3/YOUR-KEY")
        balance = await web3_service.get_balance(address)
    """
    
    def __init__(
        self,
        provider_url: Optional[str] = None,
        chain_id: int = 1,  # 1 = Ethereum mainnet
        private_key: Optional[str] = None
    ):
        """
        Initialize Web3 service
        
        Args:
            provider_url: RPC endpoint URL (e.g., Infura, Alchemy)
            chain_id: Network chain ID (1=Ethereum, 137=Polygon, etc.)
            private_key: Optional private key for signing transactions
        """
        self.provider_url = provider_url or os.getenv("WEB3_PROVIDER_URL")
        self.chain_id = chain_id
        self.private_key = private_key or os.getenv("WEB3_PRIVATE_KEY")
        self.web3 = None
        self.account = None
        
        logger.info(f"Web3Service initialized for chain {chain_id}")
    
    def connect(self) -> bool:
        """
        Connect to Web3 provider
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Lazy import to avoid requiring web3.py if not used
            from web3 import Web3
            
            if not self.provider_url:
                logger.warning("No Web3 provider URL configured")
                return False
            
            self.web3 = Web3(Web3.HTTPProvider(self.provider_url))
            
            if self.web3.is_connected():
                logger.info(f"Connected to Web3 provider (Chain ID: {self.chain_id})")
                
                # Set up account if private key provided
                if self.private_key:
                    self.account = self.web3.eth.account.from_key(self.private_key)
                    logger.info(f"Account loaded: {self.account.address}")
                
                return True
            else:
                logger.error("Failed to connect to Web3 provider")
                return False
                
        except ImportError:
            logger.error("web3.py not installed. Install with: pip install web3")
            return False
        except Exception as e:
            logger.error(f"Web3 connection error: {e}")
            return False
    
    async def get_balance(self, address: str) -> Optional[float]:
        """
        Get ETH/native token balance for an address
        
        Args:
            address: Wallet address
            
        Returns:
            Balance in ETH/native token, or None if error
        """
        try:
            if not self.web3:
                self.connect()
            
            if not self.web3:
                return None
            
            balance_wei = self.web3.eth.get_balance(address)
            balance_eth = self.web3.from_wei(balance_wei, 'ether')
            
            logger.info(f"Balance for {address}: {balance_eth} ETH")
            return float(balance_eth)
            
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None
    
    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction details dict or None
        """
        try:
            if not self.web3:
                self.connect()
            
            if not self.web3:
                return None
            
            tx = self.web3.eth.get_transaction(tx_hash)
            return dict(tx)
            
        except Exception as e:
            logger.error(f"Error getting transaction: {e}")
            return None
    
    async def send_transaction(
        self,
        to_address: str,
        value_eth: float,
        gas_limit: int = 21000
    ) -> Optional[str]:
        """
        Send native token transaction
        
        Args:
            to_address: Recipient address
            value_eth: Amount in ETH/native token
            gas_limit: Gas limit for transaction
            
        Returns:
            Transaction hash or None
        """
        try:
            if not self.web3 or not self.account:
                logger.error("Web3 not connected or no account loaded")
                return None
            
            # Build transaction
            tx = {
                'from': self.account.address,
                'to': to_address,
                'value': self.web3.to_wei(value_eth, 'ether'),
                'gas': gas_limit,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'chainId': self.chain_id
            }
            
            # Sign transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            return None
    
    async def call_contract_function(
        self,
        contract_address: str,
        abi: List[Dict],
        function_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Call a read-only contract function
        
        Args:
            contract_address: Smart contract address
            abi: Contract ABI
            function_name: Function to call
            *args: Function arguments
            **kwargs: Additional options
            
        Returns:
            Function return value
        """
        try:
            if not self.web3:
                self.connect()
            
            if not self.web3:
                return None
            
            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(contract_address),
                abi=abi
            )
            
            function = getattr(contract.functions, function_name)
            result = function(*args).call()
            
            logger.info(f"Contract function {function_name} called successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error calling contract function: {e}")
            return None
    
    async def execute_contract_function(
        self,
        contract_address: str,
        abi: List[Dict],
        function_name: str,
        *args,
        gas_limit: int = 200000,
        **kwargs
    ) -> Optional[str]:
        """
        Execute a state-changing contract function
        
        Args:
            contract_address: Smart contract address
            abi: Contract ABI
            function_name: Function to execute
            *args: Function arguments
            gas_limit: Gas limit
            **kwargs: Additional options
            
        Returns:
            Transaction hash or None
        """
        try:
            if not self.web3 or not self.account:
                logger.error("Web3 not connected or no account loaded")
                return None
            
            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(contract_address),
                abi=abi
            )
            
            function = getattr(contract.functions, function_name)
            
            # Build transaction
            tx = function(*args).build_transaction({
                'from': self.account.address,
                'gas': gas_limit,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'chainId': self.chain_id
            })
            
            # Sign and send
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Contract function {function_name} executed: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error executing contract function: {e}")
            return None
    
    def verify_signature(
        self,
        message: str,
        signature: str,
        expected_address: str
    ) -> bool:
        """
        Verify a signed message
        
        Args:
            message: Original message
            signature: Signature to verify
            expected_address: Expected signer address
            
        Returns:
            True if signature is valid
        """
        try:
            if not self.web3:
                self.connect()
            
            if not self.web3:
                return False
            
            from eth_account.messages import encode_defunct
            
            message_hash = encode_defunct(text=message)
            recovered_address = self.web3.eth.account.recover_message(
                message_hash,
                signature=signature
            )
            
            is_valid = recovered_address.lower() == expected_address.lower()
            logger.info(f"Signature verification: {is_valid}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    async def get_gas_price(self) -> Optional[int]:
        """
        Get current gas price
        
        Returns:
            Gas price in wei or None
        """
        try:
            if not self.web3:
                self.connect()
            
            if not self.web3:
                return None
            
            gas_price = self.web3.eth.gas_price
            logger.info(f"Current gas price: {gas_price} wei")
            
            return gas_price
            
        except Exception as e:
            logger.error(f"Error getting gas price: {e}")
            return None
    
    def to_checksum_address(self, address: str) -> str:
        """
        Convert address to checksum format
        
        Args:
            address: Ethereum address
            
        Returns:
            Checksummed address
        """
        if not self.web3:
            self.connect()
        
        if self.web3:
            return self.web3.to_checksum_address(address)
        
        return address
