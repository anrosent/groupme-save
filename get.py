#!/usr/bin/env python3
import json
import sys
import argparse
from urllib.error import HTTPError
from urllib.request import urlopen, Request

def make_url(groupid, before_id):
    qs = "?before_id=%s" % before_id if before_id is not None else ""
    return "https://api.groupme.com/v3/groups/%s/messages%s" % (groupid, qs)

def messages(groupid, token, before_id=None):
    url = make_url(groupid, before_id)
    headers = {"X-Access-Token": token}
    req = Request(url, headers=headers)
    res = urlopen(req)
    data = json.loads(res.read().decode('utf8'))
    if data['meta']['code'] != 200:
        raise Exception("Request failed w/ HTTP code %s" % data['meta']['code'])
    return data['response']['count'], data['response']['messages']

def init(groupid, token):
    count, msgs = messages(groupid, token)
    most_recent = msgs[-1]
    before_id = most_recent['id']
    return count, before_id

def get(groupid, token):
    history = {}
    count, msg_id = init(groupid, token) 
    print("Extracting %s messages..." % count)
    while True:
        try:
            _, msgs = messages(groupid, token, msg_id)
            if len(msgs):
                for msg in msgs:
                    history[msg['id']] = msg
                    msg_id = msg['id']
                print("Extracted %s messages" % len(history))
        except HTTPError as e:
            if e.getcode() == 304:
                break
            else:
                raise e
    return history

def from_config(fn):
    with open(fn, 'r') as f:
        opts = dict(map(lambda l: l.strip().split(), f))
        return opts['groupid'], opts['token']


def persist(history, f):
    f.write(json.dumps(history))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', metavar='config_file',help='Config file containing the token and groupid of your chatroom')
    parser.add_argument('-i', metavar='groupid', help='The ID of the chatroom you want to pull')
    parser.add_argument('-t', metavar='token', help='The X-Access-Token header Groupme gave you on login')
    parser.add_argument('-o', metavar='outfile', help='Filename you want to write the history to')
    args = parser.parse_args()

    if not args.f and not (args.i and args.t):
        parser.print_usage()
        sys.exit(1)

    if args.f:
        groupid, token = from_config(args.f)
        print("Parameters:\n\tGroupId:%s\n\tToken:%s" % (groupid, token))
                
    else:
        groupid, token = args.i, args.t

    out = sys.stdout if not args.o else open(args.o, 'w')
    history = get(groupid, token)
    persist(history, out)
