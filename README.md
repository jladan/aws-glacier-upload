AWS Glacier Backup Tool
=======================

A tool to make large backups on AWS S3 Glacier simple and reliable. The specs
are:
1. Read in credentials from a file
2. Command-line input of file name, vault, etc.
2. Log everything in a file to track passage
   - ID of multi-part upload job
   - SHA256 tree hash of each part
   - Chunk Size
   - successful completion of each part
   - successful completion of the whole
4. Place filename, description, and archive ID in database (probably a tsv)
   after job is complete
