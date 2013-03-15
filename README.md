# Gate Middleware for Swift

A middleware provider for Swift that gives Swift the ability to process forensic
data. Swift is a distributed object storage system designed to scale from a
single machine to thousands of servers. Swift is optimized for multi-tenancy and
high concurrency. Swift is ideal for backups, web and mobile content, and any
other unstructured data that can grow without bound, but with this middleware it
is ideal for forensics storage and processing of data.

With Swift REST-based API architecture, and the Gate middleware your forensic
environment is accessable through the same API.

The Gate REST-based API fully documented at http://doc.gateforensics.com/.
The Swift REST-based API fully documented at http://doc.openstack.org/.

## Development Status
This software is still in planning stage, many things could and will change.

## Enable Gate for Swift

  * proxy-server.conf

    [pipeline:main]
    pipeline = catch_errors cache tempauth gatemiddleware proxy-server

    [....]

    [filter:gatemiddleware]
    use = egg:gateswift#gatemiddleware
    amqp_connection = amqp://guest:guest@localhost/

## Swift Storage
For the Gate forensic architecture to work correctly meta data is set on
containers and objects so that the Gate Forensic Suite knows how to find and
process the data.

One container is to be used per case, allowing one or more pieces of evidence
to be added and processed for that case. A piece of evidence in a case is just
an object inside of the container. Meta data must be set on the container
pointing to the evidence, so Gate can find and process the data.

  * X-Gate-Evidence: evidence/1
  * X-Gate-Evidence: evidence/2
  * ...
  * X-Gate-Evidence: evidence/n

The evidence image that is uploaded into the container is either a single file
or a manifest file pointing to the segments of the file. If the image file is
larger than segment size set on upload then the file is segmented into chunks,
with a manifest file pointing to the chunks.

The evidence object can have metadata set for Gate to display and use. Example
below is the hashing algorithms that Gate can use to verify the image.

  * X-Object-Meta-Gate-MD5: FULLMD5SUMFOREVIDENCE
  * X-Object-Meta-Gate-SHA1: FULLSHA1SUMOFEVIDENCE
  * X-Object-Meta-Gate-SHA256: FULLSHA256SUMOFEVIDENCE
  * X-Object-Meta-Gate-SHA512: FULLSHA512SUMOFEVIDENCE
  * X-Object-Meta-Gate-BLAKE2: FULLBLAKE3SUMOFEVIDENCE

## Gate Engine
Once evidence is uploaded you then want the Gate Engine to take the evidence
and process it so the forensic information can be pulled out. For this to be
done there is metadata that can be set on the evidence.

### Verification
Gate can verify that the evidence has not been modified by using the hash values
that were set in the metadata. To start the verification process set a comma
seperated list of the algorithms to verify for. That algorithm value should
exist on the evidence already or it will be skipped.

  * X-Gate-Verify: MD5,SHA1,BLAKE2

Once the verification process has started, or finished, the Gate Engine will set
metadata on the evidence object to show that it is done verifing. Metadata will
be set giving the calculated hash for the given algorithms.

  * X-Object-Meta-Gate-Verify: MD5,SHA1,BLAKE2
  * X-Object-Meta-Gate-Verify-MD5-Status: Verified
  * X-Object-Meta-Gate-Verify-MD5: FULLMD5SUMFOREVIDENCE
  * X-Object-Meta-Gate-Verify-SHA1-Status: Verified
  * X-Object-Meta-Gate-Verify-SHA1: FULLSHA1SUMOFEVIDENCE
  * X-Object-Meta-Gate-Verify-BLAKE2-Status: Verified
  * X-Object-Meta-Gate-Verify-BLAKE2: FULLBLAKE3SUMOFEVIDENCE

### Processing
To start default processing for the evidence add the following metadata to the
container. This will instruct Gate Engine to process the evidence with default
settings. Other values can be used besides Default but these should corrispond
to the name of processing modules set in Gate Engine.

  * X-Gate-Process: Default

Once the procesing has started or has finished then Gate Engine will set
metadata on the container to show that it is done processing. Other metadata
will be set as well giving information on the result of the processing.

  * X-Container-Meta-Gate-Process: Default
  * X-Container-Meta-Gate-Process-Status: Working | Error | Success
  * X-Container-Meta-Gate-Process-Result: evidence/1/[root]/

### Results
Once processing is complete the filesystem(s) structure will be exposed in the
Swift structure, allowing individual files, and meta data, to be viewed. The
evidence is exposed like it is mounted as a huge disk and each partition is a
folder on the disk, located under the [root] folder. Below is examples of
different paths to files and folders that could be exposed.

  * evidence/1/[root]/Untitled [NTFS]/Windows/System32/
  * evidence/1/[root]/Untitled [NTFS]/Users/Administrator/AppData/

Each object in the results can have metadata that describes and gives a better
understanding of that file when it was in the filesystem. Example below is set
on [root] describing if the evidence was GPT, MBR, or no partition table.

  * X-Object-Meta-Gate-Parts-Type: GPT | MBR | None

Now when the metadata comes from the file itself and exists on the filesystem
and it was not put there by Gate, then it has a structure like below. {FS}
being the type of filesystem the file was on, {Key} being the key used in the
filesystem, and {Value} being the actual value from the filesystem.

  * X-Object-Meta-Gate-{FS}-{Key}: {Value}

### Summary
A summary of the evidence can also be retrieved giving you an overview of what
type of information the evidence held. List of all extensions and filetypes
that exist, number of items, number of deleted items, number of allocated
items, etc. To get this information a GET can be made to the evidence
container with summary as the object name.

  * GET: /account/container/summary

### Query
Gate also provides the ability to query the case, evidence, or a specfic path
in the evidence. To perform this a header is set on the request, giving the
query information. X-Gate-Query should be set on the GET request with the query
information to perform. Below is an example on how to query the case for all
files that have the extension .exe.

  * X-Gate-Query: extension=exe



