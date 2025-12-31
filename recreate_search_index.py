# from azure.search.documents.indexes import SearchIndexClient
# from azure.search.documents.indexes.models import (
#     SearchIndex, SearchField, SimpleField, SearchableField, SearchFieldDataType
# )
# from azure.core.credentials import AzureKeyCredential
# from app.core.config import settings

# endpoint = settings.AZURE_SEARCH_ENDPOINT
# key = settings.AZURE_SEARCH_KEY
# index_name = settings.AZURE_SEARCH_INDEX_NAME


# client = SearchIndexClient(endpoint, AzureKeyCredential(key))

# try:
#     client.delete_index(index_name)
# except Exception:
#     pass

# fields = [
#     SimpleField(name="id", type=SearchFieldDataType.String, key=True),
#     SearchableField(name="brand", type=SearchFieldDataType.String),
#     SearchableField(name="product_name", type=SearchFieldDataType.String),
#     SearchableField(name="category", type=SearchFieldDataType.String, filterable=True),
#     SearchableField(name="shade", type=SearchFieldDataType.String),
#     SimpleField(name="price", type=SearchFieldDataType.Double),
#     SimpleField(name="average_rating", type=SearchFieldDataType.Double),
#     SimpleField(name="total_reviews", type=SearchFieldDataType.Int32),
#     SimpleField(name="in_stock", type=SearchFieldDataType.Boolean),
#     SimpleField(name="image_url", type=SearchFieldDataType.String),
#     SimpleField(name="product_url", type=SearchFieldDataType.String),
#     # 👇 explicit string form ensures correct array type
#     SearchField(name="tags", type="Collection(Edm.String)", searchable=True, filterable=True),
#     SearchField(name="ingredients", type="Collection(Edm.String)", searchable=True, filterable=True),
# ]

# index = SearchIndex(name=index_name, fields=fields)
# client.create_index(index)
# print("✅ Created index with array fields.")

# from azure.search.documents.indexes import SearchIndexClient
# from azure.core.credentials import AzureKeyCredential

# from app.core.config import settings

# endpoint = settings.AZURE_SEARCH_ENDPOINT
# key = settings.AZURE_SEARCH_KEY
# client = SearchIndexClient(endpoint, AzureKeyCredential(key))

# print("🔎 Existing indexes:")
# for idx in client.list_indexes():
#     print("  -", idx.name)


# from azure.search.documents.indexes import SearchIndexClient
# from app.core.config import settings
# from azure.core.credentials import AzureKeyCredential
# index_client = SearchIndexClient(settings.AZURE_SEARCH_ENDPOINT, AzureKeyCredential(settings.AZURE_SEARCH_KEY))
# index = index_client.get_index(settings.AZURE_SEARCH_INDEX_NAME)

# for f in index.fields:
#     print(f"{f.name}: {f.type}")
# from azure.search.documents import SearchClient
# from azure.core.credentials import AzureKeyCredential

# endpoint = settings.AZURE_SEARCH_ENDPOINT
# key = settings.AZURE_SEARCH_KEY
# index_name = "products-index-v2"

# search_client = SearchClient(endpoint, index_name, AzureKeyCredential(key))

# doc = {
#     "id": "1",
#     "brand": "Dior",
#     "product_name": "Test Product",
#     "category": "other",
#     "price": 0.0,
#     "average_rating": 4.5,
#     "total_reviews": 0,
#     "in_stock": True,
#     "image_url": "",
#     "product_url": "",
#     "tags": ["makeup", "foundation"],
#     "ingredients": ["Aqua (Water)", "Dimethicone"]
# }

# result = search_client.upload_documents([doc])
# print("Upload result:", result)


from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from app.core.config import settings
endpoint = settings.AZURE_SEARCH_ENDPOINT
key = settings.AZURE_SEARCH_KEY

client = SearchIndexClient(endpoint, AzureKeyCredential(key))
idx = client.get_index("products-index-v2")

for f in idx.fields:
    print(f.name, "→", f.type)
