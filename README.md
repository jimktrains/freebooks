freebooks
=========

Distributed Ledger utilizing git for synchronization.

Basic Ideas
-----------

* master key - Random AES-256 key stored with repo and encrypted with "ledger password." This is used encrypt fields for each record, such as the transaction amount and a description of the transaction.  It is also used to encrypt the account names and metadata.
* user key - Random ECC key stored for each user. Private key encrypted with user password. Used to sign commits.
* commit signature - Each time a commit happens, 4 pieces of information as signed: 1) the sha for the tree of all added or modified files. 2) the unix timestamp. 3) username, 4) parent commit's sha
* all users are trusted - If someone has the ledger password and a key-pair it is assumed that they will not act maliciously. However, valid clients will never accept a forced commit and will not work on an in-valid repository

This should prevent any one person from rewriting any commit including and before the last commit not done by them.

*NOTE:* Passwords are mimiced at the moment because I got tired of typing the same dummy password in all the time. They can be enabled by removing the first return in the SymEncPasswordKey.get_password function
Example
-------

To initialize a ledger:

    python freebooks.py -l test-ledger init jim "Jim K" jim@example.com

To add a user:

    python freebooks.py -l test-ledger -u jim add-user you "You There" you@example.com

Now, let's move some money around and look at balances. (Note: account ids don't have to be numeric.  They're strings and will eventually be a .-separated hierarchy)

    python freebooks.py -u jim -l test-ledger tx 1 2 jim 100

    python freebooks.py -u jim -l test-ledger bal

    1      |   -100
    2      |    100

    python freebooks.py -u jim -l test-ledger tx 2 1 jim 400

    python freebooks.py -u jim -l test-ledger bal

    1      |    300
    2      |   -300

    python freebooks.py -u jim -l test-ledger tx 3 1 jim 200

    python freebooks.py -u jim -l test-ledger bal

    1      |    500
    3      |   -200
    2      |   -300
