# Web3 Service Documentation

A base service class for blockchain and Web3 interactions that can be extended by add-ons for specific use cases.

## Features

- ✅ **Wallet Management** - Connect wallets and manage accounts
- ✅ **Balance Queries** - Check ETH/token balances
- ✅ **Transactions** - Send native tokens
- ✅ **Smart Contracts** - Read and write contract functions
- ✅ **Signature Verification** - Verify signed messages
- ✅ **Multi-Chain Support** - Ethereum, Polygon, BSC, etc.
- ✅ **Gas Price Tracking** - Get current gas prices

## Installation

### Required Dependencies

```bash
pip install web3
```

### Environment Variables

```bash
# .env
WEB3_PROVIDER_URL=https://mainnet.infura.io/v3/YOUR-PROJECT-ID
WEB3_PRIVATE_KEY=your-private-key-here  # Optional, for signing transactions
```

## Basic Usage

### 1. Initialize Service

```python
from core.services import Web3Service

# With environment variables
web3_service = Web3Service()

# Or with explicit configuration
web3_service = Web3Service(
    provider_url="https://mainnet.infura.io/v3/YOUR-KEY",
    chain_id=1,  # 1 = Ethereum mainnet
    private_key="your-private-key"  # Optional
)

# Connect to provider
web3_service.connect()
```

### 2. Check Balance

```python
# Get ETH balance
balance = await web3_service.get_balance("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
print(f"Balance: {balance} ETH")
```

### 3. Send Transaction

```python
# Send 0.1 ETH
tx_hash = await web3_service.send_transaction(
    to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    value_eth=0.1,
    gas_limit=21000
)
print(f"Transaction: {tx_hash}")
```

### 4. Interact with Smart Contracts

```python
# Read from contract (no gas required)
contract_abi = [...]  # Your contract ABI
result = await web3_service.call_contract_function(
    contract_address="0x...",
    abi=contract_abi,
    function_name="balanceOf",
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
)

# Write to contract (requires gas)
tx_hash = await web3_service.execute_contract_function(
    contract_address="0x...",
    abi=contract_abi,
    function_name="transfer",
    "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    1000000000000000000,  # 1 token (18 decimals)
    gas_limit=100000
)
```

## Advanced Features

### Signature Verification

```python
# Verify a signed message
is_valid = web3_service.verify_signature(
    message="Hello, Web3!",
    signature="0x...",
    expected_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
)
```

### Gas Price Tracking

```python
# Get current gas price
gas_price = await web3_service.get_gas_price()
print(f"Gas price: {gas_price} wei")
```

### Address Checksumming

```python
# Convert to checksum format
checksum_addr = web3_service.to_checksum_address("0x742d35cc6634c0532925a3b844bc9e7595f0beb")
```

## Multi-Chain Support

### Ethereum Mainnet
```python
web3_service = Web3Service(
    provider_url="https://mainnet.infura.io/v3/YOUR-KEY",
    chain_id=1
)
```

### Polygon
```python
web3_service = Web3Service(
    provider_url="https://polygon-rpc.com",
    chain_id=137
)
```

### Binance Smart Chain
```python
web3_service = Web3Service(
    provider_url="https://bsc-dataseed.binance.org",
    chain_id=56
)
```

### Arbitrum
```python
web3_service = Web3Service(
    provider_url="https://arb1.arbitrum.io/rpc",
    chain_id=42161
)
```

## Extending for Add-Ons

### Example: NFT Service

```python
from core.services import Web3Service

class NFTService(Web3Service):
    """Extended service for NFT operations"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.erc721_abi = [...]  # ERC-721 ABI
    
    async def get_nft_owner(self, contract_address: str, token_id: int) -> str:
        """Get NFT owner"""
        return await self.call_contract_function(
            contract_address=contract_address,
            abi=self.erc721_abi,
            function_name="ownerOf",
            token_id
        )
    
    async def transfer_nft(
        self,
        contract_address: str,
        to_address: str,
        token_id: int
    ) -> str:
        """Transfer NFT"""
        return await self.execute_contract_function(
            contract_address=contract_address,
            abi=self.erc721_abi,
            function_name="transferFrom",
            self.account.address,
            to_address,
            token_id
        )
```

### Example: DeFi Service

```python
class DeFiService(Web3Service):
    """Extended service for DeFi operations"""
    
    async def swap_tokens(
        self,
        router_address: str,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int
    ) -> str:
        """Swap tokens on DEX"""
        router_abi = [...]
        
        return await self.execute_contract_function(
            contract_address=router_address,
            abi=router_abi,
            function_name="swapExactTokensForTokens",
            amount_in,
            min_amount_out,
            [token_in, token_out],
            self.account.address,
            int(time.time()) + 300,  # 5 min deadline
            gas_limit=300000
        )
```

## Error Handling

```python
try:
    balance = await web3_service.get_balance(address)
    if balance is None:
        print("Failed to get balance")
except Exception as e:
    logger.error(f"Web3 error: {e}")
```

## Security Best Practices

### 1. Private Key Management
- ✅ **Never** commit private keys to version control
- ✅ Use environment variables
- ✅ Consider using hardware wallets for production
- ✅ Implement key rotation policies

### 2. Transaction Safety
- ✅ Always verify recipient addresses
- ✅ Set appropriate gas limits
- ✅ Implement transaction confirmation checks
- ✅ Use nonce management for concurrent transactions

### 3. Contract Interactions
- ✅ Verify contract addresses
- ✅ Audit contract ABIs
- ✅ Test on testnets first
- ✅ Implement slippage protection for swaps

## Common Chain IDs

| Network | Chain ID | RPC URL |
|---------|----------|---------|
| **Ethereum Mainnet** | 1 | https://mainnet.infura.io/v3/YOUR-KEY |
| **Goerli Testnet** | 5 | https://goerli.infura.io/v3/YOUR-KEY |
| **Polygon** | 137 | https://polygon-rpc.com |
| **BSC** | 56 | https://bsc-dataseed.binance.org |
| **Arbitrum** | 42161 | https://arb1.arbitrum.io/rpc |
| **Optimism** | 10 | https://mainnet.optimism.io |
| **Avalanche** | 43114 | https://api.avax.network/ext/bc/C/rpc |

## Use Cases

### 1. NFT Marketplace
- Mint NFTs
- Transfer ownership
- List for sale
- Verify authenticity

### 2. DeFi Platform
- Token swaps
- Liquidity provision
- Yield farming
- Staking

### 3. DAO Governance
- Proposal creation
- Voting
- Treasury management
- Token distribution

### 4. Web3 Authentication
- Wallet connection
- Message signing
- Signature verification
- Session management

## Testing

```python
# Test on Goerli testnet
web3_service = Web3Service(
    provider_url="https://goerli.infura.io/v3/YOUR-KEY",
    chain_id=5
)

# Get test ETH from faucet: https://goerlifaucet.com/
```

---

**Note:** This is a base class designed for extension. Add-ons should inherit from `Web3Service` and implement specific blockchain functionality.
