const IPFS = require('ipfs-http-client');
const fs = require('fs');

// Connect to the IPFS API
const ipfs = IPFS.create();

// Read the content of the text file
const fileContent = fs.readFileSync('example.txt');

// Add the file to IPFS
ipfs.add(fileContent).then(result => {
  const cid = result.cid.toString();
  console.log('File added to IPFS. CID:', cid);
}).catch(error => {
  console.error('Error adding file to IPFS:', error);
});
