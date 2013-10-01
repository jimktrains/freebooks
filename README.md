freebooks
=========

Distributed Ledger utilizing git for synchronization.

All information is stored in 3 branches within git:

* key - master key
* users - Stores all user records
* tx - Stores all transaction records

Data is stored and signed within the commit itself

* Summary - Human readable description of the action
* Signature - Signature of the record
* Data - The raw data describing the action
* Actor - User ID. Stored as part of the git commit normally
* Time - The commit time. Stored as part of the git commit normally
* Parent - The commits' parents. Stored as part of the git commit normally

Since data is stored with in the commits, batch processing programs (_e.g._: GUI or webservice) may find it benificial to cache data-to-read in a database.

Basic Ideas
-----------

* master key - Random AES-256 key stored with repo and encrypted with "ledger password." This is used encrypt fields for each record, such as the transaction amount and a description of the transaction.  It is also used to encrypt the account names and metadata.
* user key - Random ECC key stored for each user. Private key encrypted with user password. Used to sign commits.
* commit signature - Each time a commit happens, 5 pieces of information as signed: 1) the sha for the tree of all added or modified files. 2) the unix timestamp. 3) username, 4) parent commits' SHAs, 5) human readable description
* all users are trusted - If someone has the ledger password and a key-pair it is assumed that they will not act maliciously. However, valid clients will never accept a forced commit and will not work on an in-valid repository
* clocks will be assumed to be correct - Most uses of this won't need split-second precisions and will normally have lots of human error as well (the time it takes to enter the tx from the time it was made).  Thus, I'm making the assumption that I can order tx by their commit time, which should be more than enough from most, if not all, cases.
* All tx amounts are stored as ints. Eventually I would like to store the currency and format of the field as well (in a per-account manner)

This should prevent any one person from rewriting any commit including and before the last commit not done by them.

*NOTE:* Passwords are mimicked at the moment because I got tired of typing the same dummy password in all the time. They can be enabled by removing the first return in the SymEncPasswordKey.get_password function

Example
-------

Try the `init_test` script or longhand

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

    python freebooks.py -u you -l test-ledger tx 3 1 jim 200

    python freebooks.py -u jim -l test-ledger bal

    1      |    500
    3      |   -200
    2      |   -300

    python freebooks.py -u jim -l test-ledger ls 1

          Jim K <jim@example.com>|1380584575|3     |1     |jim   |   200
      You There <you@example.com>|1380584570|2     |1     |jim   |   400
          Jim K <jim@example.com>|1380584567|2     |1     |jim   |  -100
