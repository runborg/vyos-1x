# Copyright 2019 VyOS maintainers and contributors <maintainers@vyos.io>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

import os

from jinja2 import Environment
from jinja2 import FileSystemLoader
from vyos.defaults import directories
from vyos.util import chmod, chown, makedir

# reuse the same Environment to improve performance
_templates_env = {
    False: Environment(loader=FileSystemLoader(directories['templates'])),
    True:  Environment(loader=FileSystemLoader(directories['templates']), trim_blocks=True),
}
_templates_mem = {
    False: {},
    True: {},
}

def vyos_address_from_cidr(text):
    """ Take an IPv4/IPv6 CIDR prefix and convert the network to an "address".
    Example:
    192.0.2.0/24 -> 192.0.2.0, 2001:db8::/48 -> 2001:db8::
    """
    from ipaddress import ip_network
    return ip_network(text).network_address

def vyos_netmask_from_cidr(text):
    """ Take an IPv4/IPv6 CIDR prefix and convert the prefix length to a "subnet mask".
    Example:
    192.0.2.0/24 -> 255.255.255.0, 2001:db8::/48 -> ffff:ffff:ffff::
    """
    from ipaddress import ip_network
    return ip_network(text).netmask

def render(destination, template, content, trim_blocks=False, formater=None, permission=None, user=None, group=None):
    """
    render a template from the template directory, it will raise on any errors
    destination: the file where the rendered template must be saved
    template: the path to the template relative to the template folder
    content: the dictionary to use to render the template

    This classes cache the renderer, so rendering the same file multiple time
    does not cause as too much overhead. If use everywhere, it could be changed
    and load the template from python environement variables from an import
    python module generated when the debian package is build
    (recovering the load time and overhead caused by having the file out of the code)
    """

    # Create the directory if it does not exists
    folder = os.path.dirname(destination)
    makedir(folder, user, group)

    # Setup a renderer for the given template
    # This is cached and re-used for performance
    if template not in _templates_mem[trim_blocks]:
        _env = _templates_env[trim_blocks]
        _env.filters['address_from_cidr'] = vyos_address_from_cidr
        _env.filters['netmask_from_cidr'] = vyos_netmask_from_cidr
        _templates_mem[trim_blocks][template] = _env.get_template(template)

    template = _templates_mem[trim_blocks][template]

    # As we are opening the file with 'w', we are performing the rendering
    # before calling open() to not accidentally erase the file if the
    # templating fails
    content = template.render(content)

    if formater:
        content = formater(content)

    # Write client config file
    with open(destination, 'w') as f:
        f.write(content)

    chmod(destination, permission)
    chown(destination, user, group)

def render_to_variable(template, content, trim_blocks=False, formater=None, permission=None, user=None, group=None):
    """
    render a template from the template directory, it will raise on any errors
    destination: the file where the rendered template must be saved
    template: the path to the template relative to the template folder
    content: the dictionary to use to render the template

    This classes cache the renderer, so rendering the same file multiple time
    does not cause as too much overhead. If use everywhere, it could be changed
    and load the template from python environement variables from an import
    python module generated when the debian package is build
    (recovering the load time and overhead caused by having the file out of the code)

    NB! This if now a copy of render(), it needs to be rewritten so render and this uses the same generation code
    """

    # Setup a renderer for the given template
    # This is cached and re-used for performance
    if template not in _templates_mem[trim_blocks]:
        _env = _templates_env[trim_blocks]
        _env.filters['address_from_cidr'] = vyos_address_from_cidr
        _env.filters['netmask_from_cidr'] = vyos_netmask_from_cidr
        _templates_mem[trim_blocks][template] = _env.get_template(template)

    template = _templates_mem[trim_blocks][template]

    content = template.render(content)

    if formater:
        content = formater(content)

    return content
