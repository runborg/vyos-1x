#!/usr/bin/env python3
#
# Copyright (C) 2020 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from sys import exit

from vyos import ConfigError
from vyos.config import Config
from vyos.util import call
from vyos.template import render
from vyos import frr
from vyos import airbag
airbag.enable()

config_file = r'/tmp/ripd.frr'

def get_config():
    conf = Config()
    base = ['protocols', 'rip']
    rip_conf = {
        'rip_conf'          : False,
        'default_distance'  : [],
        'default_originate' : False,
        'rip'  : {
            'default_metric'   : None,
            'distribute'       : {},
            'neighbors'        : {},
            'networks'         : {},
            'net_distance'     : {},
            'passive_iface'    : {},
            'redist'           : {},
            'route'            : {},
            'ifaces'           : {},
            'timer_garbage'    : 120,
            'timer_timeout'    : 180,
            'timer_update'     : 30
        }
    }

    if not (conf.exists(base) or conf.exists_effective(base)):
        return None

    if conf.exists(base):
        rip_conf['rip_conf'] = True

    conf.set_level(base)

    # Get default distance
    if conf.exists('default-distance'):
        rip_conf['default_distance'] = conf.return_value('default-distance')

    # Get default information originate (originate default route)
    if conf.exists('default-information originate'):
        rip_conf['default_originate'] = True

    # Get default-metric
    if conf.exists('default-metric'):
        rip_conf['rip']['default_metric'] = conf.return_value('default-metric')

    conf.set_level(base)

    # Get distribute list interface 
    for dist_iface in conf.list_nodes('distribute-list interface'):
        # Set level 'distribute-list interface ethX'
        conf.set_level((str(base)) + ' distribute-list interface ' + dist_iface)
        rip_conf['rip']['distribute'].update({
        dist_iface : {
            'iface_access_list_in': conf.return_value('access-list in'.format(dist_iface)),
            'iface_access_list_out': conf.return_value('access-list out'.format(dist_iface)),
            'iface_prefix_list_in': conf.return_value('prefix-list in'.format(dist_iface)),
            'iface_prefix_list_out': conf.return_value('prefix-list out'.format(dist_iface))
            }
        })

        # Access-list in
        if conf.exists('access-list in'.format(dist_iface)):
            rip_conf['rip']['iface_access_list_in'] = conf.return_value('access-list in'.format(dist_iface))
        # Access-list out
        if conf.exists('access-list out'.format(dist_iface)):
            rip_conf['rip']['iface_access_list_out'] = conf.return_value('access-list out'.format(dist_iface))
        # Prefix-list in
        if conf.exists('prefix-list in'.format(dist_iface)):
            rip_conf['rip']['iface_prefix_list_in'] = conf.return_value('prefix-list in'.format(dist_iface))
        # Prefix-list out
        if conf.exists('prefix-list out'.format(dist_iface)):
            rip_conf['rip']['iface_prefix_list_out'] = conf.return_value('prefix-list out'.format(dist_iface))

    conf.set_level((str(base)) + ' distribute-list')

    # Get distribute list, access-list in
    if conf.exists('access-list in'):
        rip_conf['rip']['dist_acl_in'] = conf.return_value('access-list in')

    # Get distribute list, access-list out
    if conf.exists('access-list out'):
        rip_conf['rip']['dist_acl_out'] = conf.return_value('access-list out')

    # Get ditstribute list, prefix-list in
    if conf.exists('prefix-list in'):
        rip_conf['rip']['dist_prfx_in'] = conf.return_value('prefix-list in')

    # Get distribute list, prefix-list out
    if conf.exists('prefix-list out'):
        rip_conf['rip']['dist_prfx_out'] = conf.return_value('prefix-list out')

    conf.set_level(base)

    # Get network Interfaces
    if conf.exists('interface'):
        rip_conf['rip']['ifaces'] = conf.return_values('interface')

    # Get neighbors
    if conf.exists('neighbor'):
        rip_conf['rip']['neighbors'] = conf.return_values('neighbor')

    # Get networks
    if conf.exists('network'):
        rip_conf['rip']['networks'] = conf.return_values('network')

    # Get network-distance
    for net_dist in conf.list_nodes('network-distance'):
        rip_conf['rip']['net_distance'].update({
            net_dist : {
                'access_list' : conf.return_value('network-distance {0} access-list'.format(net_dist)),
                'distance' : conf.return_value('network-distance {0} distance'.format(net_dist)),
            }
        })

    if conf.exists('passive-interface'):
        rip_conf['rip']['passive_iface'] = conf.return_values('passive-interface')

    # Get redistribute
    for protocol in conf.list_nodes('redistribute'):
        rip_conf['rip']['redist'].update({
            protocol : {
                'metric' : conf.return_value('redistribute {0} metric'.format(protocol)),
                'route_map' : conf.return_value('redistribute {0} route-map'.format(protocol)),
            }
        })

    conf.set_level(base)

    # Get route
    if conf.exists('route'):
        rip_conf['rip']['route'] = conf.return_values('route')

    # Get timers garbage
    if conf.exists('timers garbage-collection'):
        rip_conf['rip']['timer_garbage'] = conf.return_value('timers garbage-collection')

    # Get timers timeout
    if conf.exists('timers timeout'):
        rip_conf['rip']['timer_timeout'] = conf.return_value('timers timeout')

    # Get timers update
    if conf.exists('timers update'):
        rip_conf['rip']['timer_update'] = conf.return_value('timers update')

    return rip_conf

def verify(rip):
    if rip is None:
        return None

    # Check for network. If network-distance acl is set and distance not set
    for net in rip['rip']['net_distance']:
        if not rip['rip']['net_distance'][net]['distance']:
            raise ConfigError(f"Must specify distance for network {net}")

def generate(rip):
    if rip is None:
        return None

    # As there for now are no method for rendering a template without saving it to a file
    # we save the template and rereading it to apply it
    render(config_file, 'frr/rip.reload.frr.tmpl', rip)
    return None

def apply(rip):
    if rip is None:
        return None

    if not os.path.exists(config_file):
        raise OSError(f'File config_file not found')

    # Save original configration prior to starting any commit actions
    rip['original_config'] = frr.get_configuration(daemon='ripd')

    # As there for now are no method for rendering a template without saving it to a file
    # we save the template and rereading it to apply it
    with open(config_file, 'r') as c_file:
        repl_config = c_file.read()

    # Replace configuration in the original script
    # The before_re parameter is normally not needed, but because of a bug in the vyos.frr.replace_section function we need to add it.
    new_config = frr.replace_section(rip['original_config'], repl_config, from_re='router rip', before_re=r'(line vty)')

    print('--------- DEBUGGING ----------')
    print(f'Existing config: \n {rip["original_config"]} \n\n')
    print(f'Replacement config: \n {repl_config} \n\n')
    print(f'New config: \n {new_config} \n\n')

    # Frr Mark configuration will test for syntax errors and exception out if any syntax errors are detected prior to commiting
    frr.mark_configuration(new_config)

    # Commit the resulting new configuration to frr, this will render an frr.CommitError() Exception on fail
    frr.reload_configuration(new_config, daemon='ripd')

    # call(f'vtysh -d ripd -f {config_file}')
    # as part of debugging we do not remove the config file after its applied
    # os.remove(config_file)

    return None


def rollback(rip):
    if 'original_config' not in rip:
        print('Applying configuration failed and there were nothing to roll back to')
        return None

    try:
        frr.reload_configuration(rip['original_config'], daemon='ripd')
    except frr.CommitError as e:
        print('Failed to reapply old configuration')
        print(e)

    return None


if __name__ == '__main__':
    try:
        c = get_config()
        verify(c)
        generate(c)
        try:
            apply(c)
        except frr.CommitError as e:
            print('Commit error, Rolling back')
            print(e)
            rollback(c)
            raise
    except ConfigError as e:
        print(e)
        exit(1)
