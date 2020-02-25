AWS Glacier Backup Tool
=======================

**in progress**

A tool to make large backups on AWS S3 Glacier simple and reliable. The design requirements
are:
1. Read in credentials from a file (done)
2. Command-line input of file name, vault, etc. (done)
2. Log everything in a file to track passage
   - ID of multi-part upload job (done)
   - SHA256 tree hash of each part (done)
   - Chunk Size (not-done)
   - successful completion of each part (done)
   - successful completion of the whole (done)
4. Place filename, description, and archive ID in database (probably a tsv)
   after job is complete (basically done)

## Installation

This package is not on PyPI yet. To install, download the source, navigate to the directory, and install with pip. All dependencies should be installed automatically

1. With git:
```
git clone https://github.com/jladan/aws-glacier-upload
cd aws-glacier-upload
pip install .
```

2. Using the zipped archive:
```
wget https://github.com/jladan/aws-glacier-upload/archive/master.zip; 
unzip master.zip
cd aws-glacier-upload-master
pip install .
```

## Running

The usage information and options can be viewed with `backup.py -h`. The script pulls the credentials and basic config from the `~/.aws/`, so the AWS CLI has to be configured first.

Basic usage example:
```
backup.py -v myvault -r us-east-2 -d "this is a sample archive upload" myarchive.tar.gz
```
