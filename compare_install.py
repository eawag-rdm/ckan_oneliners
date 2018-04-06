# _*_ coding: utf-8 _*_


""" Assume we are in the CKAN virtualenv.

"""
import subprocess as sp
import re
import os.path

def get_loaded_plugins(host='localhost',
                       pasterpath='/usr/lib/ckan/default/bin/paster',
                       configpath='/etc/ckan/default/development.ini'):
    '''Returns loaded plugins for <host>.
    Assumes password-less login possible for remote host.

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

        
# plugins = get_loaded_plugins()

# pluginsr = get_loaded_plugins(host='eaw-ckan-prod1',
#                               configpath='/etc/ckan/default/production.ini')

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







