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
    if host == 'localhost':
        cmd = 'git -C {} show --pretty=oneline -q'.format(srcdir)
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
    #hostname1 = re.search(r'
    # CONTINUE HERE
    mapA = plugin_src_map(host1)
    mapB = plugin_src_map(host2)


    # for p in AandB:
    #     print(p)
    #     srcdirA = mapA[p]
    #     commit = get_commit(srcdirA, host1)
    #     print(commit)

report('https://data.eawag.ch')

          

# basedir = '/home/vonwalha/Ckan/ckan/lib/default/src/ckan/'
basedir = '/usr/lib/ckan/default/src/ckan'
defplugsl = get_defined_plugins(basedir, host='localhost')
defplugsr = get_defined_plugins(basedir, host='eaw-ckan-prod1')


local_srcdirs = get_srcdirs()
remote_srcdirs = get_srcdirs('eaw-ckan-prod1')

res = plugin_src_map('eaw-ckan-prod1')


# NEXT : allow alternative definition of entry_points, as in ckanext-scheming.
# Prepare dict as: { plugin-name: (srcdir, commit) }
# Read actually loaded plugins
# Filter directories to include only loaded plugins
# Compare loaded plugins: report
# For corresponding plugins, compare commit, report.







