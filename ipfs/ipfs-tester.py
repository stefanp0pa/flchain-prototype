import ipfshttpclient

def write_to_ipfs(file_path):
    # Connect to the local IPFS node
    client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001")

    # Add the file to IPFS
    res = client.add(file_path)
    
    # Get the CID (Content Identifier) of the uploaded file
    cid = res['Hash']
    
    print(f"File uploaded to IPFS with CID: {cid}")
    
    # Return the CID for later retrieval
    return cid

def read_from_ipfs(cid, output_path):
    # Connect to the local IPFS node
    client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001")

    # Get the file content from IPFS using the CID
    file_content = client.cat(cid)

    # Write the content to a new file
    with open(output_path, 'wb') as output_file:
        output_file.write(file_content)

    print(f"File retrieved from IPFS and saved to {output_path}")

# Example usage:
file_to_upload = "/Users/stefan/ssi-proiect/ipfs/python-file-tester.txt"
output_file_path = "/Users/stefan/ssi-proiect/ipfs/python-file-tester-output.txt"

# Write the file to IPFS and get the CID
cid = write_to_ipfs(file_to_upload)

# Read the file back from IPFS using the CID
read_from_ipfs(cid, output_file_path)
