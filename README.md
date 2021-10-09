# Coding test

- Give execution permission to 'start.sh' file.

    `chmod u+x ./start.sh`

- Start the containers

    `./start.sh`

- Put json files to sent in **./data/to_send** folder.

- Received files are located in **./data/received** folder.

- Files already sent are moved to **./data/sent**

- There are also error folders corresponding to error when sending or receiving files (**./data/sent_error** and **./data/received_error**).

- There are some files for testing in **./data/files_for_testing**

---
## Notes

- Next steps could be:

	- Include a database to store information about sent and received files.
