from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = False
        result['failed'] = False

        is_borg_server = False

        for hostname, hostvars in task_vars['hostvars'].items() :
            if 'borg_server' in hostvars.keys() and hostvars['borg_server'] == task_vars['ansible_host']:
                is_borg_server = True

        result['ansible_facts'] = {
            'is_borg_server': is_borg_server,
        }

        return result

