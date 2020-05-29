from vyos.config import Config
from pprint import pprint
import os
import sys

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
    'interfaces-loopback': 'interfaces loopback',
    'interfaces-dummy': 'interfaces dummy',
    'interfaces-ethernet': 'interfaces ethernet',
    'interfaces-pseudo-ethernet': 'interfaces pseudo-ethernet',
    'interfaces-bonding': 'interfaces bonding',
    'interfaces-bridge': 'interfaces bridge',
    'interfaces-pppoe': 'interfaces pppoe',
    'interfaces-wireless': 'interfaces wireless',
    'interfaces-wirelessmodem': 'interfaces wirelessmodem',
    'interfaces-geneve': 'interfaces geneve',
    'interfaces-tunnel': 'interfaces tunnel',
    'interfaces-wireguard': 'interfaces wireguard',
    'interfaces-vxlan': 'interfaces vxlan',
}


def is_changed(path):
    # As a quick and dirty workaround, a simple string compare is done on both trees
    return conf.show_config(path.split(" "), effective=True) != conf.show_config(path.split(" "), effective=False)


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
    path = module_search_paths[module]    
    if conf.is_tag(path):
        # This is a tag node, run configurator for every child-node
        for node in conf.list_nodes(path):
            n = f"{path} {node}"
            if is_changed(n):
                modules_to_run.append((module, n))
                print(f"*  Tag for module {module}/{n} has changes")
    elif is_changed(path):
        # This is a "normal" node, just run on the whole node
        print(f"*  Module {module} has changes")
        modules_to_run.append((module, path))
    else:
        # Nothing is changed"
        print(f"*  Module {module} is clean")

print()
print("Modules scheduled for execution:  " + ", ".join([f"{_[0]}/{_[1]}" for _ in modules_to_run]))


configs = {}
# Main Executor
# First we run get_config, because the configuraxwtor gets the tag value from an
# env variable, we need to set that in advance
print("Starting Execution")
for module, path in modules_to_run:
    # Get the tag and pass it to the configurator
    os.environ["VYOS_TAGNODE_VALUE"] = path[-1]
    # Executing get_config for module
    print(f"*  Running get_config for {module}/{path}")
    configs[(module, path)] = modules[module].get_config()


# Execute verify
for module, path in modules_to_run:
    # TODO: check if verify script exists before executing
    print(f"*  Running verify for {module}/{path}")
    modules[module].verify(configs[(module, path)])


# Critical loop generating config
# Execute verify
generated_modules = []
try:
    for module, path in modules_to_run:
        # TODO: check if generate script exists before executing
        # TODO: Make it do a rollback on all executed modules on a fail
        # TODO: should the current running module also rollback?
        print(f"*  Running Generate for {module}/{path}")
        generated_modules.append((module, path))
        modules[module].generate(configs[(module, path)])
except Exception as e:
    print("OOOps, something went wrong.. wee need to do a rollback")
    print("Rolling back all previously executed steps")
    print(e)
    for module, path in generated_modules:
        if not hasattr(module, "rollback"):
            print(f"*  {module} has no rollback capabilities.. your system migth be in limbo")
            continue
        # Do the rollback something like this
        modules[module].rollback(configs[(module, path)])
    print("Done, exiting and failing commit")
    sys.exit(1)


# Wee also need to do the same logic on a failed apply
# but that needs to rollback both generate and apply

generated_modules = []
try:
    for module, path in modules_to_run:
        # TODO: check if generate script exists before executing
        # TODO: Make it do a rollback on all executed modules on a fail
        # TODO: should the current running module also rollback?
        print(f"*  Running Apply for {module}/{path}")
        generated_modules.append((module, path))
        modules[module].apply(configs[(module, path)])
except Exception as e:
    print("OOOps, something went wrong.. wee need to do a rollback")
    print("Rolling back all previously executed steps")
    print(e)
    for module, path in generated_modules:
        if not hasattr(module, "rollback"):
            print(f"*  {module} has no rollback capabilities.. your system migth be in limbo")
            continue
        print("Que?")
        # Do the rollback something like this
        modules[module].rollback(configs[(module, path)])
        modules[module].apply(configs[(module, path)])

    print("Done, exiting and failing commit")
    sys.exit(1)


print("Dump of generated config")
pprint(configs)
