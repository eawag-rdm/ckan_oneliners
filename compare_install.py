# _*_ coding: utf-8 _*_


""" Assume we are in the CKAN virtualenv.

"""
# ckanbasedir = '/usr/lib/ckan/default/'
# execfile(os.path.join(ckanbasedir, 'bin/activate_this.py'),
#          dict(__file__= os.path.join(ckanbasedir, 'bin/activate_this.py')))         


import subprocess as sp
import ckanapi
import re
import os.path


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
    entry_point_pat  = re.compile(r'entry_points\s*=\s*{.*?}', flags = re.DOTALL)
    plugin_list_pat = re.compile(r'\'ckan.plugins\'\s*:\s*(\[.*?\])',
                                 flags = re.DOTALL)
    entry_points = re.search(entry_point_pat, setup).group()
    pluginlist =  re.search(plugin_list_pat, entry_points).groups(0)[0]
    pluginstrings = eval(pluginlist)
    plugins = [x.split('=')[0].strip() for x in pluginstrings]
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
    return dirs
        
def get_commit(srcdir, host='localhost'):
    "Returns identifying line for checked-out commit."
    if host == 'localhost':
        cmd = 'git -C {} show --pretty=oneline -q'.format(srcdir)
        proc = sp.Popen(cmd.split(), stdout=sp.PIPE)
        commit = proc.communicate()[0].split()[0]
    return commit



resultset = {
    'loaded_A': [],
    'loaded_B': [],
    'commit_A': [],
    'commit_B': [],
    'srcdir': []
}
         
def report(host1, host2='http://localhost:5000'):
    A = get_extensions(host=host1)
    B = get_extensions(host=host2)
    
    AandB = sorted(list(set(A['extensions']) & set(B['extensions'])))
    onlyA = sorted(list(set(A['extensions']) - set(B['extensions'])))
    onlyB = sorted(list(set(B['extensions']) - set(A['extensions'])))
    print('\nVersion {}: {}\n'.format(host1, A['version']))
    print('\nVersion {}: {}\n'.format(host2, B['version']))
    print('\nPlugins loaded in {}, not in {}:\n{}'.format(host1, host2, onlyA))
    print('\nPlugins loaded in {}, not in {}:\n{}'.format(host2, host1, onlyB))

report('https://data.eawag.ch')

          

# basedir = '/home/vonwalha/Ckan/ckan/lib/default/src/ckan/'
# basedir = '/usr/lib/ckan/default/src/ckan'
# defplugsl = get_defined_plugins(basedir, host='localhost')
# defplugsr = get_defined_plugins(basedir, host='eaw-ckan-prod1')


local_srcdirs = get_srcdirs()

# restrict to one
lscr = local_srcdirs[1]

commit = get_commit(lscr)
defplugs = get_defined_plugins(lscr)


# NEXT : allow alternative definition of entry_points, as in ckanext-scheming.
# Prepare dict as: { plugin-name: (srcdir, commit) }
# Read actually loaded plugins
# Filter directories to include only loaded plugins
# Compare loaded plugins: report
# For corresponding plugins, compare commit, report.







