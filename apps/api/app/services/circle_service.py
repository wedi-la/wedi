"""
Circle HTTP API service for developer-controlled wallets.

This implementation uses direct HTTP requests instead of the circle-developer-controlled-wallets
package to avoid Pydantic version conflicts.
"""
import base64
import hmac
import hashlib
import json
import time
import uuid
from typing import Dict, List, Optional, Any

from starlette.datastructures import URL
from app.core.logging import get_logger
from app.core.config import settings
from app.core.exceptions import ExternalServiceError
import httpx

logger = get_logger()


class CircleService:
    """Service for interacting with Circle developer-controlled wallets."""

    def __init__(self) -> None:
        """Initialize the Circle service with API key and entity secret."""
        try:
            self.api_key = settings.CIRCLE_API_KEY
            self.entity_secret = settings.CIRCLE_ENTITY_SECRET
            self.api_url = f"{settings.CIRCLE_API_URL}/v1/w3s"
            self.client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0
            )
            self.initialized = True
            logger.info("circle_service_initialized")
        except Exception as e:
            logger.error("circle_service_init_failed", error=str(e))
            self.initialized = False
            raise ExternalServiceError(
                message=f"Failed to initialize Circle service: {str(e)}",
                service="circle"
            )
            self.initialized = True
            logger.info("circle_service_initialized")
        except Exception as e:
            logger.error("circle_service_init_failed", error=str(e))
            self.initialized = False
            raise ExternalServiceError(
                message=f"Failed to initialize Circle service: {str(e)}",
                service="circle"
            )

    def _generate_entity_secret_ciphertext(self) -> str:
        """
        Generate entity secret ciphertext required for certain API calls.
        
        Returns:
            str: Base64 encoded entity secret HMAC
        """
        timestamp = str(int(time.time() * 1000))
        message = timestamp.encode('utf-8')
        secret = self.entity_secret.encode('utf-8')
        
        signature = hmac.new(secret, message, digestmod='sha256').digest()
        encoded_signature = base64.b64encode(signature).decode('utf-8')
        
        return f"{timestamp}.{encoded_signature}"
        
    async def create_wallet_set(self, name: str) -> Dict[str, Any]:
        """
        Create a new wallet set in Circle.

        Args:
            name: Name for the wallet set

        Returns:
            Dict[str, Any]: The created wallet set details
        """
        try:
            url = f"{self.api_url}/developer/walletSets"
            
            # Generate entity secret ciphertext
            entity_secret_ciphertext = self._generate_entity_secret_ciphertext()
            
            payload = {
                "name": name,
                "entitySecretCiphertext": entity_secret_ciphertext
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            logger.info("created_wallet_set", wallet_set_id=result["data"]["walletSet"]["id"])
            return result["data"]["walletSet"]
        except httpx.HTTPError as e:
            logger.error("create_wallet_set_failed", error=str(e))
            raise ExternalServiceError(
                message=f"Failed to create wallet set: {str(e)}",
                service="circle"
            )

    async def get_wallet_sets(self) -> List[Dict[str, Any]]:
        """
        Get all wallet sets.

        Returns:
            List[Dict[str, Any]]: List of wallet sets
        """
        try:
            url = f"{self.api_url}/developer/walletSets"
            response = await self.client.get(url)
            response.raise_for_status()
            result = response.json()
            return result["data"]["walletSets"]
        except httpx.HTTPError as e:
            logger.error("get_wallet_sets_failed", error=str(e))
            raise ExternalServiceError(
                message=f"Failed to get wallet sets: {str(e)}",
                service="circle"
            )

    async def get_wallet_set(self, wallet_set_id: str) -> Dict[str, Any]:
        """
        Get wallet set by ID.

        Args:
            wallet_set_id: The wallet set ID

        Returns:
            Dict[str, Any]: Wallet set details
        """
        try:
            url = f"{self.api_url}/developer/walletSets/{wallet_set_id}"
            response = await self.client.get(url)
            response.raise_for_status()
            result = response.json()
            return result["data"]["walletSet"]
        except httpx.HTTPError as e:
            logger.error("get_wallet_set_failed", error=str(e), wallet_set_id=wallet_set_id)
            raise ExternalServiceError(
                message=f"Failed to get wallet set: {str(e)}",
                service="circle"
            )

    async def update_wallet_set(self, wallet_set_id: str, name: str) -> Dict[str, Any]:
        """
        Update a wallet set.

        Args:
            wallet_set_id: The wallet set ID
            name: New name for the wallet set

        Returns:
            Dict[str, Any]: Updated wallet set details
        """
        try:
            url = f"{self.api_url}/developer/walletSets/{wallet_set_id}"
            
            # Generate entity secret ciphertext
            entity_secret_ciphertext = self._generate_entity_secret_ciphertext()
            
            payload = {
                "name": name,
                "entitySecretCiphertext": entity_secret_ciphertext
            }
            
            response = await self.client.put(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            return result["data"]["walletSet"]
        except httpx.HTTPError as e:
            logger.error("update_wallet_set_failed", error=str(e), wallet_set_id=wallet_set_id)
            raise ExternalServiceError(
                message=f"Failed to update wallet set: {str(e)}",
                service="circle"
            )

    async def create_wallet(
        self, 
        wallet_set_id: str, 
        blockchain: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new wallet within a wallet set.

        Args:
            wallet_set_id: The wallet set ID
            blockchain: Blockchain identifier (e.g., "MATIC-MUMBAI")
            metadata: Optional metadata for the wallet

        Returns:
            Dict[str, Any]: The created wallet
        """
        try:
            url = f"{self.api_url}/developer/wallets"
            
            # Generate entity secret ciphertext
            entity_secret_ciphertext = self._generate_entity_secret_ciphertext()
            
            # Set up request with required fields
            payload = {
                "walletSetId": wallet_set_id,
                "blockchains": [blockchain],
                "count": 1,  # Create a single wallet
                "accountType": "SCA",  # Smart Contract Account type
                "entitySecretCiphertext": entity_secret_ciphertext
            }
            
            # Add optional metadata if provided
            if metadata:
                payload["metadata"] = metadata
                
            # Make the API call
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if not result["data"] or not result["data"]["wallets"] or len(result["data"]["wallets"]) == 0:
                raise ExternalServiceError(
                    message="Failed to create wallet: empty response",
                    service="circle"
                )
                
            # Get the created wallet (first in the list)
            wallet = result["data"]["wallets"][0]
            
            logger.info(
                "created_wallet", 
                wallet_id=wallet["id"], 
                wallet_set_id=wallet_set_id, 
                blockchain=blockchain
            )
            
            return wallet
        except httpx.HTTPError as e:
            logger.error(
                "create_wallet_failed", 
                error=str(e), 
                wallet_set_id=wallet_set_id, 
                blockchain=blockchain
            )
            raise ExternalServiceError(
                message=f"Failed to create wallet: {str(e)}",
                service="circle"
            )

    async def get_wallets(self, wallet_set_id: str) -> List[Dict[str, Any]]:
        """
        Get all wallets in a wallet set.

        Args:
            wallet_set_id: The wallet set ID

        Returns:
            List[Dict[str, Any]]: List of wallets
        """
        try:
            url = f"{self.api_url}/developer/wallets?walletSetId={wallet_set_id}"
            response = await self.client.get(url)
            response.raise_for_status()
            result = response.json()
            return result["data"]["wallets"]
        except httpx.HTTPError as e:
            logger.error("get_wallets_failed", error=str(e), wallet_set_id=wallet_set_id)
            raise ExternalServiceError(
                message=f"Failed to get wallets: {str(e)}",
                service="circle"
            )

    async def get_wallet(self, wallet_set_id: str, wallet_id: str) -> Dict[str, Any]:
        """
        Get wallet by ID.

        Args:
            wallet_set_id: The wallet set ID
            wallet_id: The wallet ID

        Returns:
            Dict[str, Any]: Wallet details
        """
        try:
            url = f"{self.api_url}/developer/wallets/{wallet_id}?walletSetId={wallet_set_id}"
            response = await self.client.get(url)
            response.raise_for_status()
            result = response.json()
            return result["data"]["wallet"]
        except httpx.HTTPError as e:
            logger.error(
                "get_wallet_failed",
                error=str(e),
                wallet_set_id=wallet_set_id,
                wallet_id=wallet_id
            )
            raise ExternalServiceError(
                message=f"Failed to get wallet: {str(e)}",
                service="circle"
            )

    async def get_wallet_addresses(
        self, 
        wallet_set_id: str, 
        wallet_id: str
    ) -> List[Dict[str, str]]:
        """
        Get addresses for a wallet.

        Args:
            wallet_set_id: The wallet set ID
            wallet_id: The wallet ID

        Returns:
            List[Dict[str, str]]: List of addresses with blockchain info
        """
        try:
            url = f"{self.api_url}/developer/wallets/{wallet_id}/addresses?walletSetId={wallet_set_id}"
            response = await self.client.get(url)
            response.raise_for_status()
            result = response.json()
            return result["data"]["addresses"]
        except httpx.HTTPError as e:
            logger.error(
                "get_wallet_addresses_failed",
                error=str(e),
                wallet_id=wallet_id,
                wallet_set_id=wallet_set_id
            )
            raise ExternalServiceError(
                message=f"Failed to get wallet addresses: {str(e)}",
                service="circle"
            )

    async def get_balances(self, wallet_set_id: str, wallet_id: str) -> List[Dict[str, Any]]:
        """
        Get token balances for a wallet.

        Args:
            wallet_set_id: The wallet set ID
            wallet_id: The wallet ID

        Returns:
            List[Dict[str, Any]]: List of token balances
        """
        try:
            url = f"{self.api_url}/developer/wallets/{wallet_id}/balances?walletSetId={wallet_set_id}"
            response = await self.client.get(url)
            response.raise_for_status()
            result = response.json()
            return result["data"]["tokenBalances"]
        except httpx.HTTPError as e:
            logger.error(
                "get_balances_failed",
                error=str(e),
                wallet_id=wallet_id,
                wallet_set_id=wallet_set_id
            )
            raise ExternalServiceError(
                message=f"Failed to get wallet balances: {str(e)}",
                service="circle"
            )
    async def create_transaction(
        self, 
        *, 
        wallet_id: str,
        destination: str,
        amount: str,
        token_id: str = "USDC",
        fee_level: str = "MEDIUM",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new transaction from a wallet.
        
        Args:
            wallet_id: The Circle wallet ID
            destination: Destination blockchain address
            amount: Amount to send (as string)
            token_id: Token ID to send (default: USDC)
            fee_level: Transaction fee level (default: MEDIUM)
            idempotency_key: Optional idempotency key
            
        Returns:
            Dict containing transaction details
        """
        try:
            logger.info("Creating wallet transaction", wallet_id=wallet_id)
            
            # Generate entity secret ciphertext
            entity_secret_ciphertext = self._generate_entity_secret_ciphertext()
            
            url = f"{self.api_url}/developer/wallets/{wallet_id}/transfer"
            
            # Create transaction payload
            payload = {
                "idempotencyKey": idempotency_key or str(uuid.uuid4()),
                "entitySecretCiphertext": entity_secret_ciphertext,
                "amount": {
                    "amount": amount,
                    "currency": token_id
                },
                "destination": {
                    "address": destination,
                    "chain": self._map_token_to_chain(token_id)
                },
                "feeLevel": fee_level
            }
            
            # Execute transaction
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            logger.info(
                "Created wallet transaction", 
                wallet_id=wallet_id,
                transaction_id=result["data"]["transfer"]["id"]
            )
            logger.debug("Transaction response", response=result)
            
            return result["data"]["transfer"]
            
        except httpx.HTTPError as e:
            logger.error(
                "Failed to create wallet transaction", 
                wallet_id=wallet_id, 
                error=str(e)
            )
            raise ExternalServiceError(f"Failed to create transaction: {e}")
        except Exception as e:
            logger.error(
                "Unexpected error creating wallet transaction", 
                wallet_id=wallet_id, 
                error=str(e)
            )
            raise ExternalServiceError(f"Unexpected error: {e}")
    
    async def get_wallet_transactions(
        self,
        *,
        wallet_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page_size: int = 10,
        page_number: int = 1,
    ) -> Dict[str, Any]:
        """
        Get transactions for a specific wallet.
        
        Args:
            wallet_id: The Circle wallet ID
            from_date: Optional start date (ISO format)
            to_date: Optional end date (ISO format)
            page_size: Number of results per page
            page_number: Page number for pagination
            
        Returns:
            Dict containing transaction list and pagination info
        """
        try:
            logger.info("Getting wallet transactions", wallet_id=wallet_id)
            
            # Build URL with query params
            url = f"{self.api_url}/developer/wallets/{wallet_id}/transfers?pageSize={page_size}&pageNumber={page_number}"
            
            if from_date:
                url += f"&from={from_date}"
                
            if to_date:
                url += f"&to={to_date}"
            
            response = await self.client.get(url)
            response.raise_for_status()
            result = response.json()
            
            logger.debug("Got wallet transactions response", response=result)
            
            return result["data"]
            
        except httpx.HTTPError as e:
            logger.error(
                "Failed to get wallet transactions", 
                wallet_id=wallet_id, 
                error=str(e)
            )
            raise ExternalServiceError(f"Failed to get wallet transactions: {e}")
    
    def _map_token_to_chain(self, token_id: str) -> str:
        """
        Map token ID to blockchain chain identifier.
        
        Args:
            token_id: The token identifier
            
        Returns:
            str: The blockchain chain identifier
        """
        # Default mapping for common tokens
        token_chain_map = {
            "USDC": "ETH",            # Ethereum
            "USDC_AVAX": "AVAX",     # Avalanche
            "USDC_MATIC": "MATIC",   # Polygon
            "USDC_ARB": "ARB",       # Arbitrum
            "USDC_BASE": "BASE",     # Base
            "USDC_OP": "OP",         # Optimism
            "USDC_SOL": "SOL",       # Solana
        }
        
        return token_chain_map.get(token_id, "ETH")  # Default to Ethereum


# Singleton instance
circle_service = CircleService()
