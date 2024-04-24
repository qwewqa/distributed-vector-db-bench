from pinecone import Pinecone, ServerlessSpec
from pinecone_datasets import load_dataset
# from constants import PINECONE_API_KEY
import pandas as pd
import numpy as np
import time

BATCH_SIZE = 100


def upload_data(dataset, index):
    print(f"\n Uploading Data...")
    start = time.perf_counter()
    index.upsert_from_dataframe(dataset.drop(columns=["sparse_values","metadata","blob"]))
    end = time.perf_counter()
    return (end-start)/60.0



def query(query_vectors, index, k=100):
    print(f"\n Batch Querying...")
    times = []
    results = []
    for i in range(0,10000):
        item = query_vectors[i]
        start = time.perf_counter()
        # query_results = index.query(queries=batch_items, top_k=10, disable_progress_bar=True)
        res = index.query(vector=item, top_k=k, include_values=True)
        end = time.perf_counter()
        results.append(res)
        times.append(end-start)
        print("batch done", i)
    return [times, results]

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


def run():
	glove100_dataset = load_dataset("ANN_GloVe_d100_angular")
	print("strating pinecone")
	pc = Pinecone(api_key=PINECONE_API_KEY)
	pc.delete_index("glove100d-aws")
	pc.create_index(
		name="glove100d-aws",
		dimension=100,
		metric="cosine",
		# change later, serverless only available on AWS 
		# trying to start with some boilerplate code rn git commit -am ""
		spec=ServerlessSpec(
			cloud='aws', 
			region='us-east-1'
		) 
	) 

	index = pc.Index("glove100d-aws")
	print("created index")
	dataset = glove100_dataset.documents
	print("made dataset")
	upload_latency = upload_data(dataset, index)
	query_vectors = [item.tolist() for item in glove100_dataset.queries["vector"]]
	nn = glove100_dataset.queries["blob"][0]["nearest_neighbors"]
	# query_results = glove100_dataset.queries["blob"]
	times, results = query(query_vectors, index, 10)
	print("Mean query latency",np.mean(times))
	formatted_results = formatResults(results)
	nn100 = []
	for x in glove100_dataset.queries["blob"]: 
		s = set(x["nearest_neighbors"])
		nn100.append(s)

if __name__ == "__main__":
    run()