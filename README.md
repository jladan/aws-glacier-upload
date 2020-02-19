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
