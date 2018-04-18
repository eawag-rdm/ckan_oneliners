# _*_ coding: utf-8 _*_

"""compare_install.py

Compares set of modules loaded in two CKAN instances on two different machines.
Useful to compare deployment- with development environment. Also compares the
git revison of plugins that are loaded by both apps.

Usage: compare_install.py <host1> [<host2>]

Arguments:
<host1>:   First machine in URL notation, e.g. "https://remote-server.eawag.ch".
<host2>:   Second machine in URL notation [default: http://localhost:5000]
    
Assumptions:

+ We are in the CKAN virtualenv and all hosts involved are reachable
  with passwordless ssh.

+ On the remote (deployment) server exists a directory GITBASE_REMOTE under
  which all (bare) git repositories for ckan core and the plugins are stored.
  The version that is checked out here is the deployed version.

You might want to set the constant GITBASE_REMOTE to a different path.

To temporarily set GITBASE_REMOTE or use different GITBASE_REMOTE for
host1 and host2 set environment variable(s) GITBASE_REMOTE_<normalized_hostname>.
<normalized_hostname> is the hostname this path refers to, where all
characters are uppercase and all non-alphanumerical characters have been replaced
with an underscore ("_").

Example:
GITBASE_REMOTE_DEPLOY_SERV=/home/Ckan/ckan/git python compare_install.py \
https://deploy-serv.mydomain.tld http://localhost:5000

"""

import subprocess as sp
import ckanapi
import re
import os.path
from docopt import docopt

GITBASE_REMOTE = '/home/ckan/git'

def get_loaded_plugins(host='localhost',
                       pasterpath='/usr/lib/ckan/default/bin/paster',
                       configpath='/etc/ckan/default/development.ini'):
    '''Returns loaded plugins for <host>.
    Assumes password-less login possible for remote host.
    THIS IS REDUNDANT. PREFER get_extensions() USING API-CALL

    '''
    if host == 'localhost':
        hostpart = ''
    else:
        hostpart = 'ssh {} '.format(host)
    cmd = (hostpart + pasterpath +
           ' --plugin=ckan plugin-info -c {}'.format(configpath))
    proc = sp.Popen(cmd.split(), stdout=sp.PIPE)
    out, err = proc.communicate()
    plugins = re.findall("\n(.*):\n---", out)
    plugins.sort()
    return plugins

def get_extensions(host='http://localhost:5000'):
    ckan = ckanapi.RemoteCKAN(host)
    info = ckan.call_action('status_show')
    return {'version': info['ckan_version'], 'extensions': info['extensions']}

def get_defined_plugins(basedir, host='localhost'):
    "Retrieves list of plugins from setup.py in <basedir>"
    setuppath = os.path.join(basedir, 'setup.py')
    if host != 'localhost':
        cmd = 'ssh {} cat {}'.format(host, setuppath)
        proc = sp.Popen(cmd.split(), stdout=sp.PIPE)
        setup, err = proc.communicate()
    else:
        setup = open(setuppath, 'r').read()
    entry_point_pat  = re.compile(r'entry_points\s*=\s*{.*?}', flags=re.DOTALL)
    entry_point_alt_pat = re.compile(r'\[ckan.plugins\](.*?)(\[.*?\]|"""|\'\'\')',
                                     flags=re.DOTALL)
    plugin_list_pat = re.compile(r'\'ckan.plugins\'\s*:\s*(\[.*?\])',
                                 flags=re.DOTALL)
    try:
        entry_points = re.search(entry_point_pat, setup).group()
        pluginlist =  re.search(plugin_list_pat, entry_points).groups(0)[0]
        pluginstrings = eval(pluginlist)
    except AttributeError:
        try:
            plugin_string = re.search(entry_point_alt_pat, setup).groups(0)[0]
            pluginstrings = [x.strip() for x in plugin_string.split('\n')]
            pluginstrings = [x for x in pluginstrings
                             if len(x) > 0 and x[0] != '#']
        except:
            return []
    plugins = [x.split('=')[0].strip() for x in pluginstrings if len(x) > 0]
    return plugins

def get_srcdirs(host='localhost'):
    '''Returns the list of paths that contain individually versioned codes,
    usually plugins.

    '''
    basedir = '/usr/lib/ckan/default/src'
    if host == 'localhost':
        dirs = [os.path.join(basedir, d) for d in os.listdir(basedir)]
        dirs = [d for d in dirs if os.path.isdir(d)]
    else:
        cmd = ('ssh {} find {} -type d -maxdepth 1 -mindepth 1'
               .format(host, basedir))
        proc = sp.Popen(cmd.split(), stdout=sp.PIPE)
        dirs, err = proc.communicate()
        dirs = dirs.split('\n')
        dirs = [d for d in dirs if len(d) > 0]
    return dirs
        
def get_commit(srcdir, host='localhost'):
    "Returns identifying line for checked-out commit."
    gitdir = get_gitdirs(srcdir, host)
    if host != 'localhost':
        pre ='ssh {} '.format(host)
    else:
        pre = ''
    cmd = pre + 'git -C {} log --pretty=oneline HEAD^1..HEAD'.format(gitdir)
    proc = sp.Popen(cmd.split(), stdout=sp.PIPE)
    commit = proc.communicate()[0].split()[0]
    return commit

def plugin_src_map(host='localhost'):
    mapping = {}
    srcdirs = get_srcdirs(host)
    for sd in srcdirs:
        defplugs = get_defined_plugins(sd, host=host)
        mapping.update(dict(zip(defplugs, len(defplugs)*[sd])))
    return mapping

def get_gitdirs(workdir, host='localhost'):
    '''Returns root directory of Git directory for a working
    directory. Trivial for the development machine (same). For the
    (remote) production server this is specific to the deployment
    setup. Probably needs to be adapted when used elsewhere.

    '''
   
    if host == 'localhost':
        return workdir
    else:
        gitbase_remote_envvar = re.sub(
            '[^0-9a-zA-Z]', '_',
            'GITBASE_REMOTE_' + host.split('.')[0].upper())
        gitbase_remote = os.environ.get(gitbase_remote_envvar, GITBASE_REMOTE)
        return os.path.join(gitbase_remote,
                            '{}.git'.format(os.path.basename(workdir)))
    
def report(host1, host2):
    A = get_extensions(host=host1)
    B = get_extensions(host=host2)
    
    AandB = sorted(list(set(A['extensions']) & set(B['extensions'])))
    onlyA = sorted(list(set(A['extensions']) - set(B['extensions'])))
    onlyB = sorted(list(set(B['extensions']) - set(A['extensions'])))
    print('\nVersion {}: {}\n'.format(host1, A['version']))
    print('\nVersion {}: {}\n'.format(host2, B['version']))
    print('\nPlugins loaded in {}, not in {}:\n{}'.format(host1, host2, onlyA))
    print('\nPlugins loaded in {}, not in {}:\n{}'.format(host2, host1, onlyB))
    url2hostpat = r'https?://(?P<host>.*?)(:[0-9]{1,5}$|$)'
    hostnameA = re.subn(url2hostpat, '\g<host>', host1)[0]
    hostnameB = re.subn(url2hostpat, '\g<host>', host2)[0]
    mapA = plugin_src_map(hostnameA)
    mapB = plugin_src_map(hostnameB)
    for p in AandB:
        commitA = get_commit(mapA[p], host=hostnameA)
        commitB = get_commit(mapB[p], host=hostnameB)
        if commitA != commitB:
            print('Different checked out versions for {}:\n'.format(p))
            print('{}: {}\n'.format(hostnameA, commitA))
            print('{}: {}\n'.format(hostnameB, commitB))

if __name__ == "__main__":
    args = docopt(__doc__)
    report(args['<host1>'], args['<host2>'] or 'http://localhost:5000')








