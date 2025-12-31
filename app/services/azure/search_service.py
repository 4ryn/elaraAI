"""
GlamAI - Azure AI Search Service (Complete Fixed Version)
Proper indentation and array handling
"""

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings
import logging
import asyncio
from typing import List, Optional, Dict, Any
from app.services.azure import llm_service

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        self.endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.index_name = settings.AZURE_SEARCH_INDEX_NAME
        self.credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        self.search_client = SearchClient(self.endpoint, self.index_name, self.credential)
        self.index_client = SearchIndexClient(self.endpoint, self.credential)
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Force recreate Azure Search index with correct field types."""
        try:
            logger.info(f"🔧 Recreating Azure Search index: {self.index_name}")
            print("🔍 Using endpoint:", self.endpoint)
            print("🔍 Index name:", self.index_name)

            # Always delete first to ensure schema consistency
            try:
                self.index_client.delete_index(self.index_name)
                logger.info(f"🗑️ Deleted existing index '{self.index_name}'")
            except Exception as e:
                logger.warning(f"ℹ️ No existing index to delete or already removed: {e}")

            # ✅ Define field schema explicitly
            from azure.search.documents.indexes.models import SearchField

            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="brand", type=SearchFieldDataType.String, sortable=True, filterable=True),
                SearchableField(name="product_name", type=SearchFieldDataType.String, sortable=True),
                SearchableField(name="category", type=SearchFieldDataType.String, sortable=True, filterable=True),
                SearchableField(name="shade", type=SearchFieldDataType.String, filterable=True),
                SimpleField(name="price", type=SearchFieldDataType.Double, sortable=True, filterable=True),
                SimpleField(name="average_rating", type=SearchFieldDataType.Double, sortable=True, filterable=True),
                SimpleField(name="total_reviews", type=SearchFieldDataType.Int32, sortable=True, filterable=True),
                SimpleField(name="in_stock", type=SearchFieldDataType.Boolean, filterable=True),
                SimpleField(name="image_url", type=SearchFieldDataType.String),
                SimpleField(name="product_url", type=SearchFieldDataType.String),

                # ✅ Explicitly define collection fields (string form avoids SDK type loss)
                SearchField(name="tags", type="Collection(Edm.String)", searchable=True, filterable=True),
                SearchField(name="ingredients", type="Collection(Edm.String)", searchable=True, filterable=True),
            ]

            # Create new index
            index = SearchIndex(name=self.index_name, fields=fields)
            self.index_client.create_index(index)
            logger.info(f"✅ Azure Search index '{self.index_name}' created successfully with {len(fields)} fields")

            # Verify schema after creation
            created_index = self.index_client.get_index(self.index_name)
            for f in created_index.fields:
                print(f"{f.name} → {f.type}")

        except Exception as e:
            logger.error(f"❌ Error ensuring Azure Search index: {e}")
            logger.exception("❌ Full traceback for Azure Search index creation failure:")



    async def upload_products(self, products: list[dict]):
        """
        Upload or merge product data into Azure Search.
        Properly handles Collection fields and empty arrays.
        """
        try:
            clean_products = []
            
            for p in products:
                # Get ingredients and tags
                ingredients = p.get("ingredients", [])
                tags = p.get("tags", [])
                
                # Ensure they are lists
                if not isinstance(ingredients, list):
                    ingredients = [ingredients] if ingredients else []
                if not isinstance(tags, list):
                    tags = [tags] if tags else []
                
                # Filter out empty/None values and ensure strings
                ingredients = [str(i).strip() for i in ingredients if i and str(i).strip()]
                tags = [str(t).strip() for t in tags if t and str(t).strip()]
                
                # Build clean document
                clean_doc = {
                    "id": str(p.get("id", "")),
                    "brand": str(p.get("brand") or ""),
                    "product_name": str(p.get("product_name") or "Unknown"),
                    "category": str(p.get("category") or "other"),
                    "shade": str(p.get("shade") or ""),
                    "price": float(p.get("price") or 0.0),
                    "average_rating": float(p.get("average_rating") or 0.0),
                    "total_reviews": int(p.get("total_reviews") or 0),
                    "in_stock": bool(p.get("in_stock", True)),
                    "image_url": str(p.get("image_url") or ""),
                    "product_url": str(p.get("product_url") or ""),
                }
                
                # CRITICAL FIX: Add placeholders for empty collections
                if ingredients:
                    clean_doc["ingredients"] = ingredients
                else:
                    clean_doc["ingredients"] = ["Not specified"]
                
                if tags:
                    clean_doc["tags"] = tags
                else:
                    clean_doc["tags"] = ["Untagged"]
                
                clean_products.append(clean_doc)
                logger.info(f"📦 Prepared: {clean_doc['product_name'][:50]}")
                logger.info(f"   - Ingredients: {len(clean_doc.get('ingredients', []))} items")
                logger.info(f"   - Tags: {len(clean_doc.get('tags', []))} items")

            # Upload to Azure Search
            result = self.search_client.upload_documents(documents=clean_products)
            
            # Check results
            success_count = sum(1 for r in result if r.succeeded)
            failed_count = len(result) - success_count
            
            logger.info(f"✅ Uploaded {success_count}/{len(result)} products to Azure Search")
            
            if failed_count > 0:
                logger.warning(f"⚠️ {failed_count} products failed to upload")
                for r in result:
                    if not r.succeeded:
                        logger.error(f"   Failed: {r.key} - {r.error_message}")

        except Exception as e:
            logger.error(f"❌ Failed to upload products to Azure Search: {e}")
            logger.error(f"   Products attempted: {len(products)}")
            if products:
                logger.error(f"   First product sample: {products[0]}")
            # Don't raise - allow product to be saved even if search indexing fails

    async def search_products(
        self,
        category: Optional[str] = None,
        user_profile: Optional[Dict[str, Any]] = None,
        avoid_concerns: Optional[List[str]] = None,
        avoid_allergens: Optional[List[str]] = None,
        query: Optional[str] = "*",
        max_price: Optional[float] = None,
        top: int = 10,
        enrich_results: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search with filters and optional AI enrichment
        """
        try:
            filters = ["in_stock eq true"]
            
            if category:
                filters.append(f"category eq '{category}'")
            
            if max_price:
                filters.append(f"price le {max_price}")

            filter_expr = " and ".join(filters) if filters else None

            results = self.search_client.search(
                search_text=query or "*",
                filter=filter_expr,
                top=top,
                order_by=["average_rating desc", "total_reviews desc"]
            )

            products = [dict(r) for r in results]

            # Optional AI safety enrichment
            if enrich_results and user_profile:
                enriched_products = await self._enrich_with_safety(
                    products, user_profile, avoid_concerns, avoid_allergens
                )
                return enriched_products

            return products

        except Exception as e:
            logger.error(f"❌ Product search error: {str(e)}")
            return []

    async def _enrich_with_safety(
        self,
        products: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        avoid_concerns: Optional[List[str]] = None,
        avoid_allergens: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Check each product using AI for safety."""
        tasks = []

        for product in products:
            ingredients = product.get("ingredients", [])
            product_name = product.get("product_name", "Unknown Product")

            tasks.append(
                llm_service.check_product_safety(
                    product_name=product_name,
                    product_ingredients=ingredients,
                    user_profile=user_profile
                )
            )

        safety_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(safety_results):
            if isinstance(result, Exception):
                logger.warning(f"⚠️ Safety enrichment failed for {products[i].get('product_name')}")
                products[i]["is_safe_for_user"] = True
                products[i]["safety_score"] = 0.8
                products[i]["warnings"] = []
                continue

            products[i].update({
                "is_safe_for_user": result.get("is_safe"),
                "safety_score": result.get("safety_score"),
                "safety_confidence": result.get("confidence"),
                "safety_warnings": result.get("warnings", []),
                "safety_recommendation": result.get("recommendation"),
                "severity": result.get("severity")
            })

        return products

    async def find_product_substitutes(
        self,
        category: str,
        user_profile: Dict[str, Any],
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Find budget-friendly substitutes"""
        return await self.search_products(
            category=category,
            user_profile=user_profile,
            max_price=max_price,
            query="budget-friendly",
            top=5
        )

    async def get_trending_products(
        self,
        category: Optional[str] = None,
        top: int = 10
    ) -> List[Dict[str, Any]]:
        """Get trending/popular products"""
        try:
            filter_expr = "in_stock eq true"
            if category:
                filter_expr += f" and category eq '{category}'"

            results = self.search_client.search(
                search_text="*",
                filter=filter_expr,
                select=[
                    "id", "brand", "product_name", "category", "price",
                    "image_url", "average_rating", "total_reviews"
                ],
                top=top,
                order_by=["total_reviews desc", "average_rating desc"]
            )

            return [dict(r) for r in results]

        except Exception as e:
            logger.error(f"🔥 Trending products error: {str(e)}")
            return []


# Singleton Instance
search_service = SearchService()