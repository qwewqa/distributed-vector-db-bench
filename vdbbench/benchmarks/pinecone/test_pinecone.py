from pinecone import Pinecone, ServerlessSpec
# TODO: change structure and make it functional
pc = Pinecone(api_key='YOUR_API_KEY')

pc.create_index(
    name="quickstart",
    dimension=8,
    metric="cosine",
    # change later, serverless only available on AWS 
    # trying to start with some boilerplate code rn git commit -am ""
    spec=ServerlessSpec(
        cloud='aws', 
        region='us-west-2'
    ) 
) 

index = pc.Index("quickstart")

index.upsert(
  vectors=[
    {"id": "vec1", "values": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]},
    {"id": "vec2", "values": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]},
    {"id": "vec3", "values": [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]},
    {"id": "vec4", "values": [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4]}
  ],
  namespace="ns1"
)