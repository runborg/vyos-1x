from vyos.config import Config

conf = Config()

# Module Execution order
module_exec_order = [
    'interfaces-loopback',
    'interfaces-dummy',
    'interfaces-ethernet',
    'interfaces-pseudo-ethernet',
    'interfaces-bonding',
    'interfaces-bridge',
    'interfaces-pppoe',
    'interfaces-wireless',
    'interfaces-wirelessmodem',
    'interfaces-geneve',
    'interfaces-tunnel',
    'interfaces-wireguard',
    'interfaces-vxlan',
]

module_search_paths = {
    'interfaces-loopback': (['interfaces','loopback'], 'tag'),
    'interfaces-dummy': (['interfaces', 'dummy'], 'tag'),
    'interfaces-ethernet': (['interfaces', 'ethernet'], 'tag'),
    'interfaces-pseudo-ethernet': (['interfaces', 'pseudo-ethernet'], 'tag'),
    'interfaces-bonding': (['interfaces', 'bonding'], 'tag'),
    'interfaces-bridge': (['interfaces', 'bridge'], 'tag'),
    'interfaces-pppoe': (['interfaces', 'pppoe'], 'tag'),
    'interfaces-wireless': (['interfaces', 'wireless'], 'tag'),
    'interfaces-wirelessmodem': (['interfaces', 'wirelessmodem'], 'tag'),
    'interfaces-geneve': (['interfaces', 'geneve'], 'tag'),
    'interfaces-tunnel': (['interfaces', 'tunnel'], 'tag'),
    'interfaces-wireguard': (['interfaces', 'wireguard'], 'tag'),
    'interfaces-vxlan': (['interfaces', 'vxlan'], 'tag'),
}


def is_changed(path):
  # As a quick and dirty workaround, a simple string compare is done on both trees
  return conf.show_config(path, effective=True) != conf.show_config(path, effective=False)


# Load all modules
print("Loading Modules:")
modules = {}
for module in module_exec_order:
    print(f'*  Loading {module}')
    modules[module] = __import__(f'{module}')

print("Modules successfully loaded!")
print()
print("Checking for changes in modules")
modules_to_run = []
for module in module_exec_order:
    if is_changed(module_search_paths[module][0]):
        print(f"*  Module {module} has changes")
        modules_to_run.append(module)
    else:
        print(f"*  Module {module} is clean")
print()
print("Modules scheduled for execution:  " + ", ".join(modules_to_run))


