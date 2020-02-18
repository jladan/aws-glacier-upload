""" AWS Backup tool

TODO: usage string
"""

import logging
import argparse

import io
import os
import hashlib
from functools import partial
from itertools import count

import boto3
from tqdm import tqdm

# Set up process logging
tsv = logging.getLogger('tsv')
tsv.setLevel(logging.DEBUG)
fh = logging.FileHandler('glacier-upload.log')
formatter = logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s')
fh.setFormatter(formatter)
tsv.addHandler(fh)

full_log = logging.getLogger('full')
full_log.setLevel(logging.DEBUG)
fh = logging.FileHandler('glacier-responses.log')
fh.setFormatter(logging.Formatter('%(message)s\n'))
full_log.addHandler(fh)

archive_log = logging.getLogger('archives')
archive_log.setLevel(logging.DEBUG)
fh = logging.FileHandler('glacier-archives.tsv')
fh.setFormatter(logging.Formatter('%(asctime)s\t%(message)s'))
archive_log.addHandler(fh)

def main():
    """ Main function of this script

    The `options` are passed as the result of argparse.
    """
    # Set up the command line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    # The main argument is which file to use
    parser.add_argument("file")
    parser.add_argument("-v", "--vault", help="The AWS Glacier vault")
    parser.add_argument("-p", "--profile", help="The session profile to use", default="default")
    parser.add_argument("-r", "--region", help="The region for the Glacier Vault")
    parser.add_argument("-d", "--description", help="Archive description", default='')
    options = parser.parse_args()

    upload_file(
            options.file, 
            profile=options.profile,
            region=options.region, 
            vault=options.vault, 
            description=options.description,
            partsize=2**20 * 16)

def upload_file(fname,
        profile='default',
        region='',
        vault='',
        description='',
        partsize=2**23):
    """ Upload a file in parts to the AWS vault
    """
    fsize = os.stat(fname).st_size
    session = boto3.Session(profile_name=profile)
    client = session.client('glacier', region)
    tsv.debug('Initiating the multipart upload of {}'.format(fname))
    # Upload initiation
    job_response = client.initiate_multipart_upload(
            vaultName=vault,
            archiveDescription=description,
            partSize=str(partsize),
            )
    full_log.debug(job_response)
    muid = job_response['uploadId']
    tsv.info('uploadID:%s', muid)
    # Multi-part uploading
    hashlist = upload_parts(fname, client, vault, muid, partsize, fsize)
    # Verify the locally generated hashes
    total_sha = combine_sha256(hashlist)
    full_log.debug('combined hash %s', total_sha.hexdigest())
    full_log.debug('combined hash %s', sha256tree(fname).hexdigest())
    # Close off the upload
    tsv.debug('Closing the multipart upload')
    final_response = client.complete_multipart_upload(
            vaultName=vault,
            uploadId=muid,
            checksum=total_sha.hexdigest(),
            archiveSize=str(fsize)
            )
    full_log.debug(final_response)
    tsv.info('archiveId:%s', final_response['archiveId'])
    archive_log.info('{}\t{}'.format(fname, final_response['archiveId']))
    print("Job's done!")

def abort_uploads():
    # XXX Need to get the client properly
    mpus = client.list_multipart_uploads(vaultName=vault)
    for mpu in mpus:
        client.abort_multipart_upload(vaultName=vault, uploadId=mpu['MultipartUploadId'])

def upload_parts(fname, client, vault, muid, psize, total_size=None):
    """ Upload the parts of a multipart upload job.
    """
    tsv_log = logging.getLogger('tsv')
    full_log = logging.getLogger('full')
    shas = []
    if total_size:
        noparts = total_size // psize + 1 
    else:
        noparts = 1
    with open(fname, 'rb') as f:
        for partno, chunk in tqdm(zip(count(), iter(partial(f.read, psize), b'')), total=noparts):
            start = partno * psize
            end = start + len(chunk)
            shas.append(sha256tree(chunk))
            full_log.debug('part {} sha256:{}'.format(partno, shas[-1].hexdigest()))
            response = client.upload_multipart_part(
                    vaultName=vault, 
                    uploadId=muid, 
                    checksum=shas[-1].hexdigest(), 
                    range='bytes %s-%s/*' %(start, end-1), 
                    body=chunk)
            full_log.info(response)
            tsv_log.info('part:{}\tchecksum:{}'.format(partno, response['checksum']))
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
