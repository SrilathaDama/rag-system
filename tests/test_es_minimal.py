from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "test_dense_vector"

# Delete old index if it exists
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)

# Try creating a minimal dense_vector index
mappings = {
    "mappings": {
        "properties": {
            "embedding": {
                "type": "dense_vector",
                "dims": 384,
                "index": False
            },
            "text": {"type": "text"}
        }
    }
}

es.indices.create(index=INDEX_NAME, body=mappings)
print("✅ Successfully created minimal index.")
