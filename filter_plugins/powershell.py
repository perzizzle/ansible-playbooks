import yaml
from ansible import errors


def toPowershell(x):
    try:
        powershell ="@{"
        if isinstance(x, dict):
            for key, value in x.items():
               powershell += "'{0}'='{1}';".format(key,value)
            powershell +="}"
            return powershell
        else:
            return False
    except TypeError:
        return False

class FilterModule(object):
    ''' Ansible powershell jinja2 filters '''

    def filters(self):
        return {
            # convert yaml array to powershell hash
            'toPowershell': toPowershell,

        }


