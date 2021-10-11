# Coding test

Solution fo the coding test described in file 'Docker+Python.txt'.

To start up follow these steps:

- Give execution permission to 'start.sh' and 'down.sh' file.

    `chmod u+x ./start.sh ./down.sh`

- Start the containers

    `./start.sh`

- Put json files to sent in **./data/to_send** folder (there are some files for testing in **./data/files_for_testing**).

- Received files are located in **./data/received** folder.

- Files already sent are moved to **./data/sent**.

- There are also folders corresponding to errors when sending or receiving files (**./data/sent_error** and **./data/received_error**).

- To remove containers and images execute

    `./down.sh`

---
## Notes

- We are using sockets to transmit the files over a network. Depending on the use case and/or infraestructure, we could use higher level tools like an sftp or a web server instead. Both of which could provide encryption (if we use an SSL connection for the web server). This way we don't have to worry about encrypting and decrypting the files.

- For encryption we are using a symmetric algorithm, so we assume that there is a secure way to distribute the key. If that is not the case we must use an asymmetric algorithm like RSA.

- The private key is passed as an environment variable. It could also be generated automatically while deployment with an init container.

- The slowest part of the pipeline is the conversion from json to xml which 
relies on a third party library.

- Depending on the rate of files to transmit or the size of the files, we can think of ways to optimize the code.

- Next steps could be:

	- Include a database to store information about sent and received files.
    - Support several connections at the same time.
    - Add a checksum to check the integrity of the file.
    - Write unitary and integration tests.
