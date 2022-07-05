from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = False
        result['failed'] = False

        error_msgs = []

        ### OS support #######################################################
        os_package_names = {
            'Alpine':   'borgbackup',
            'Debian':   'borgbackup',
            'FreeBSD':  'py38-borgbackup',
            'Gentoo':   'app-backup/borgbackup',
            'OpenBSD':  'borgbackup',
            'RedHat':   'borgbackup',
        }
        if task_vars['ansible_os_family'] not in os_package_names:
            error_msgs.append(f"borg role does not support {task_vars['ansible_os_family']} os family clients yet")

        ### Borg server variables ############################################
        server = {
            'clients': [],  # a list of hostnames
        }
        for hostname, hostvars in task_vars['hostvars'].items() :
            if 'borg_server' in hostvars.keys() and hostvars['borg_server'] == task_vars['ansible_host']:
                server['clients'].append({'hostname': hostname, 'pubkey': hostvars['ansible_local']['borg']['pubkey']})

        ### Borg client variables ############################################
        client = {
            'server': '',  # a server hostname
        }
        if 'borg_server' in task_vars:
            client['server'] = task_vars['borg_server']

        ### Results compilation ##############################################
        if error_msgs != []:
            result['msg'] = ' ; '.join(error_msgs)
            result['failed'] = True
            return result

        result['ansible_facts'] = {
            'borg': {
                'client': client,
                'package_name': os_package_names[task_vars['ansible_os_family']],
                'server': server,
            }
        }

        return result
