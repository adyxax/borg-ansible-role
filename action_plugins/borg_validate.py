from ansible.plugins.action import ActionBase

import re

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = False
        result['failed'] = False

        error_msgs = []

        ### host_vars validations ############################################
        if 'borg_server' in task_vars:
            # a borg server must exist
            if not isinstance(task_vars['borg_server'], str):
                error_msgs.append(f"The borg_server variable must be of type string for host {task_vars['ansible_host']}")
            elif not task_vars['borg_server'] in task_vars['hostvars'].keys():
                error_msgs.append(f"The borg_server {task_vars['borg_server']} configured for host {task_vars['ansible_host']} does not exist")
            else:
                # a borg client needs a list of jobs
                if 'borg_jobs' not in task_vars:
                    error_msgs.append(f"No borg_jobs defined for host {task_vars['ansible_host']} while it has a borg_server configured")
                elif not isinstance(task_vars['borg_jobs'], list):
                    error_msgs.append(f"The borg_jobs variable must be of type list for host {task_vars['ansible_host']}")
                else:
                    for job in task_vars['borg_jobs']:
                        # a job is a dict with specific keys
                        if not isinstance(job, dict):
                            error_msgs.append(f"The borg_jobs list elements must be of type dict for host {task_vars['ansible_host']}")
                            continue
                        for key in job.keys():
                            if not key in ['name', 'path', 'command_to_pipe', 'pre_command', 'post_command', 'exclude']:
                                error_msgs.append(f"Invalid key {key} in a job for host {task_vars['ansible_host']}")
                        # a job name is a mandatory string
                        if not 'name' in job.keys():
                            error_msgs.append(f"Invalid job for host {task_vars['ansible_host']} : no name defined")
                        elif not isinstance(job['name'], str):
                            error_msgs.append(f"Invalid job name for host {task_vars['ansible_host']} : name must be of type string")
                        elif not re.match(r'^[a-zA-Z0-9_]+$', job['name']):
                            error_msgs.append(f"Invalid job name for host {task_vars['ansible_host']} : name must match ^[a-zA-Z0-9_]+$")
                        # path and command_to_pipe are mutually exclusive
                        if 'path' in job.keys() and 'command_to_pipe' in job.keys():
                            error_msgs.append(f"Invalid job for host {task_vars['ansible_host']} : it needs either a path or a command_to_pipe, not both")
                        elif 'path' not in job.keys() and 'command_to_pipe' not in job.keys():
                            error_msgs.append(f"Invalid job for host {task_vars['ansible_host']} : it needs either a path or a command_to_pipe")
                        elif 'path' in job.keys():
                            if not isinstance(job['path'], str):
                                error_msgs.append(f"Invalid job for host {task_vars['ansible_host']} : path must be of type string")
                        elif not isinstance(job['command_to_pipe'], str):
                            error_msgs.append(f"Invalid job for host {task_vars['ansible_host']} : command_to_pipe must be of type string")
                        # a pre_command is an optional string
                        if 'pre_command' in job.keys():
                            if not isinstance(job['pre_command'], str):
                                error_msgs.append(f"Invalid job for host {task_vars['ansible_host']} : pre_command must be of type string")
                        # a post_command is an optional string
                        if 'post_command' in job.keys():
                            if not isinstance(job['post_command'], str):
                                error_msgs.append(f"Invalid job for host {task_vars['ansible_host']} : post_command must be of type string")
                        # exclude is an optional list of paths
                        if 'exclude' in job.keys():
                            if not isinstance(job['exclude'], list):
                                error_msgs.append(f"Invalid job for host {task_vars['ansible_host']} : exclude must be of type list")
                            else:
                                for path in job['exclude']:
                                    if not isinstance(path, str):
                                        error_msgs.append(f"Invalid job for host {task_vars['ansible_host']} : exclude must be a list of strings")
                # a borg client needs prune arguments
                if not 'borg_prune_arguments' in task_vars:
                    error_msgs.append(f"No borg_jobs defined for host {task_vars['ansible_host']} while it has a borg_server configured")
                elif not isinstance(task_vars['borg_prune_arguments'], str):
                        error_msgs.append(f"The borg_prune_arguments variable must be of type string for host {task_vars['ansible_host']}")

        ### Results compilation ##############################################
        if error_msgs != []:
            result['msg'] = ' ; '.join(error_msgs)
            result['failed'] = True

        return result
