#!/usr/bin/env python
# _*_ coding: utf-8 _*_

"""get_users

Retrieves list of users that have particular status.

Usage:
  get_users [-a APIKEY] [-o ORGANIZATION] [-s STATUS] [-f FILTER] HOST 
  get_users -h

Arguments:
    HOST            The web adress of the CKAN host.

Options:
  -h --help         Show this help.
  -a APIKEY         CKAN API-key (default: $CKAN_APIKEY)
  -o ORGANIZATION   Only show users of ORGANIZATION (default: all organizations).
                    [NOT YET IMPLEMENTED]
  -s STATUS         Only show users of STATUS. STATUS is a string
                    with characters in "aem", with meaning a: admin,
                    e: editor, m: member (default: all users).
  -f FILTER         Fields that should be returned, separated by comma 
                    (default: all). Ex. "fullname,email"

"""

import os
from docopt import docopt
from ckanapi import RemoteCKAN

def main(args):
    def capac(capacity):
        return (capacity[0] in args['-s']) if args['-s'] else True
    
    host = args['HOST']
    apikey = args['-a'] or os.environ.get('CKAN_APIKEY')
    ckan = RemoteCKAN(host, apikey=apikey)
    orgas = ckan.call_action('organization_list', data_dict=
                             {'all_fields': True,
                              'include_users': True})
    userids = [u['id'] for o in orgas for u in o['users']
               if capac(u['capacity'])]
    users = [ckan.call_action('user_show', data_dict={'id': uid})
             for uid in userids]
    output(users, args['-f'])

def output(users, fields):
    if fields:
        fieldlist = fields.split(',')
    else:
        fieldlist = False
    
    def fil(field):
        if fieldlist:
            return field in fieldlist
        else:
            return True
    
    def mkline(os, fn, val):
        if fieldlist and len(fieldlist) == 1:
            return os + val + ' '
        else:
            return os + '{}:{} '.format(fn, val) 
        
    for u in users:
        os = ''
        for i in u.iteritems():
            if fil(i[0]):
                os = mkline(os, i[0], i[1])
        os = os[0:-1]
        print(os)

if __name__ == '__main__':
    args = docopt(__doc__)
    main(args)
    




 

