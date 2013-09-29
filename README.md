freebooks
=========

Distributed Ledger utilizing git for synchronization.

Basic Ideas
-----------

* master key - Random AES-256 key stored with repo and encrypted with "ledger password." This is used encrypt fields for each record, such as the transaction amount and a description of the transaction.  It is also used to encrypt the account names and metadata.
* user key - Random ECC key stored for each user. Private key encrypted with user password. Used to sign commits.
* commit signature - Each time a commit happens, 4 pieces of information as signed: 1) the sha for the tree of all added or modified files. 2) the unix timestamp. 3) username, 4) parent commit's sha

This should prevent any one person from rewriting any commit including and before the last commit not done by them.

