""" AWS Backup tool

TODO: usage string
"""

import io
import hashlib
from functools import partial

import boto3

def main():
    vault = 'icicles-ladan'
    description = ''
    partsize = 2**10 * 16 # 16 Megabytes
    client = boto3.client('glacier')
    job_response = client.initiate_multipart_upload(
            vaultName=vault,
            archiveDescription=description,
            partSize=str(partsize),
            )
    hashlist = upload_parts(fname, client, vault, muid, partsize)
    total_sha = combine_sha256(hashlist)
    assert total_sha.digest() == sha256tree(fname).digest()
    final_response = client.complete_multipart_upload(
            vaultName=vault,
            uploadID=muid,
            checksum=total_sha,
            archiveSize=fsize
            )
    print("Job's done!")

def upload_parts(fname, client, vault, muid, psize):
    """ Upload the parts of a multipart upload job.
    """
    start = 0
    shas = []
    with open(fname, 'rb') as f:
        for chunk in iter(partial(f.read, psize), b''):
            chunk = f.read(psize)
            end = start + len(chunk)
            shas.append(sha256tree(chunk))
            client.upload_multipart_part(
                    vaultName=vault, 
                    uploadId=muid, 
                    checksum=shas[-1].hexdigest(), 
                    range='bytes %s-%s/*' %(start, end-1), 
                    body=chunk)
    return shas


def sha256tree(thing):
    """ Calculate the sha256 tree checksum of a bytestring.

    This is the checksum required for all AWS uploads and downloads to ensure data integrity. The process is:
    1. Chunk the data into 1MiB chunks (1024**2 bytes)
       This is arranged as a binary tree, where each leaf is a chunk.
    2. Compute the sha256 hash for each chunk (leaf)
    3. Compute the sha256 hash for each node at the next level up.
       a. Append the bytestring hash of the right-child onto that of the left-child
       b. compute the sha256 hash of the combined string.
    4. Repeat up the tree.

    The hash is needed in both raw and hex-string forms, so the sha256 object is returned.
    """
    if isinstance(thing, io.BufferedIOBase):
        bstream = thing
    elif isinstance(thing, bytes):
        bstream = io.BytesIO(thing)
    elif isinstance(thing, str):
        with open(thing, 'rb') as f:
            return sha256tree(f)
    else:
        raise ValueError('sha256 tree hash expects a byte stream or string')
    chunks = chunk_sha256(bstream)
    return combine_sha256(chunks)

def chunk_sha256(bstream):
    """ Compute the sha256 hash of each 1MiB chunk of a byte stream.
    """
    return [hashlib.sha256(c) for c in iter(partial(bstream.read, 2**20), b'')]

def combine_sha256(hashlist):
    """ Combine a list of sha256 hashes as a binary tree.
    """
    output = hashlist
    while len(output) > 1:
        lefts, rights = output[::2], output[1::2]
        new_out = [hashlib.sha256(l.digest() + r.digest()) for l, r in zip(lefts, rights)]
        if len(output) % 2 == 1:
            new_out.append(output[-1])
        output = new_out
    return output[0]

if __name__ == "__main__":
    main()
