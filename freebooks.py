import os
import argparse
import shutil

from user import User
from ledger import Ledger

parser = argparse.ArgumentParser(description='Process the ledger')
parser.add_argument('--ledger', '-l', metavar="DIR", type=str,
                   help='Path to the ledger', required=True)
parser.add_argument('--user', "-u", metavar="USER_NAME", type=str,
                   help='Acts as user')
parser.add_argument('command', type=str, help='command')
parser.add_argument('command_args', type=str, nargs='*', help='command arguments')
args = parser.parse_args()

if args.command == 'init':

    if 3 > len(args.command_args):
        raise Exception("Must specifiy a user when initializing")
    user = User(args.command_args[0], args.command_args[1], args.command_args[2])
    # FOR TESTING ONLY
    # THIS WILL ERROR
    if os.path.exists(args.ledger):
        shutil.rmtree(args.ledger)

    ledger = Ledger.init(args.ledger, user)
    
else:
    with Ledger(args.ledger, args.user) as ledger:
        if args.command == 'add-user':
            if 2 > len(args.command_args):
                raise Exception("Must specifiy a user when initializing")
            user_to_add = User(
                args.command_args[0], # Username
                args.command_args[1], # Full Name
                args.command_args[2]) # Email
            user_to_add.generate_key()
            ledger.add_user(user_to_add)
        elif args.command == "tx":
            ledger.create_tx(
                args.command_args[0], # to
                args.command_args[1], # from
                args.command_args[2], # desc
                int(args.command_args[3]) #amt
            )
        elif args.command == "balances" or args.command == 'bal':
            accts = ledger.balances()
            print'%-6s|%6s' % ("Account", "Balance")
            print'%6s-+-%6s' % (6*'-', 6*'-')
            for acct in accts:
                print'%-6s|%6d' % (acct, accts[acct])
        elif args.command == "list-tx" or args.command == 'ls':
            acct = args.command_args[0]
            for tx in ledger.txs_for_account(acct):
                if acct == tx['from_account']:
                    tx['from_account'] = tx['to_account']
                    tx['to_account'] = acct
                    tx['amount'] = -tx['amount']
                print'%30s|%-6s|%-6s|%-6s|%-6s|%6d' % (tx['who'], tx['when'], tx['from_account'], tx['to_account'], tx['description'],tx['amount'])
