from pinecone import Pinecone, ServerlessSpec
from pinecone_datasets import list_datasets, load_dataset
from constants import PINECONE_API_KEY
import pandas as pd
import numpy as np
import time

glove100_dataset = load_dataset("ANN_GloVe_d100_angular")

pc = Pinecone(api_key=PINECONE_API_KEY)
pc.create_index(
    name="glove100d",
    dimension=100,
    metric="cosine",
    # change later, serverless only available on AWS 
    # trying to start with some boilerplate code rn git commit -am ""
    spec=ServerlessSpec(
        cloud='aws', 
        region='us-west-2'
    ) 
) 

index = pc.Index("glove100d")


nn = glove100_dataset.queries["blob"][0]["nearest_neighbors"]

dataset = glove100_dataset.documents
def upload_data(dataset=dataset, index=index):
    print(f"\n Uploading Data...")
    start = time.perf_counter()
    index.upsert_from_dataframe(dataset.drop(columns=["sparse_values","metadata","blob"]))
    end = time.perf_counter()
    return (end-start)/60.0

upload_latency = upload_data()
batch_size = 100
query_vectors = np.asarray(glove100_dataset.queries["vector"])
query_results = glove100_dataset.queries["blob"]

def query(query_vectors=query_vectors, index=index, k=100):
    print(f"\n Batch Querying...")
    batch_times = []
    results = []
    for i in range(0,10000, batch_size):
        batch_items = query_vectors[i:i+batch_size]
        start = time.perf_counter()
        # query_results = index.query(queries=batch_items, top_k=10, disable_progress_bar=True)
        for item in batch_items:
            res = index.query(vector=item, top_k=k, include_values=True)
            results.append(res)
        end = time.perf_counter()
        batch_times.append(end-start)
        print("batch done", i)
    return [batch_times, results]


times, results = query()

def formatResults(results):
	formatted_results = []
		# result["matches"]
		# id = result["matches"]["id"]
		# score = result["matches"]["score"]
		# values = result["matches"]["values"]
		# x = {"id":id, "score":score, "values":values}
	for result in results:
		matches = result["matches"]
		res_matches = []
		for match in matches:
			id = match["id"]
			score = match["score"]
			values = match["values"]
			x = {"id":id, "score":score, "values":values}
			res_matches.append(x)
		formatted_results.append(res_matches)
    
	return formatted_results

formatted_results = formatResults(results)

nn100 = []
for x in glove100_dataset.queries["blob"]: 
    s = set(x["nearest_neighbors"])
    nn100.append(s)