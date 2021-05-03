This is the ansible role I use to orchestrate the backups on my personal infrastructure with [borg](https://borgbackup.readthedocs.io/en/stable/).

## Introduction

I wanted a role to easily manage my backups and did not find an existing one that satisfied me. A mandatory feature for me was the ability to configure a client in only one place without having to configure a server : the server configuration will be derived from the clients that need to use it as a backup target. Another mandatory feature is the validation of host_vars which virtually no role in the wild ever does... So I wrote [mine](https://git.adyxax.org/adyxax/borg-ansible-role).

This way configuring backups for a host named `yen.adyxax.org` is as simple as having the following `host_vars` :
```yaml
julien@yen:~/git/adyxax/ansible$ cat host_vars/yen.adyxax.org
---
borg_server: cobsd-jde.nexen.net
borg_jobs:
  - { name: etc, path: "/etc", exclude: [ "/etc/firmware" ] }
  - name: gitea
    path: "/tmp/gitea.zip"
    pre_command: "echo '/usr/local/sbin/gitea -C /etc/gitea -c /etc/gitea/app.ini dump -f /tmp/gitea.zip' | su -l _gitea"
    post_command: "rm -f /tmp/gitea.zip"
  - { name: nethack, path: "/opt/nethack" }
  - { name: var_imap, path: "/var/imap" }
  - { name: var_spool_imap, path: "/var/spool/imap" }
...
```

Which can be used in a simple playbook like :
```yaml
julien@yen:~/git/adyxax/ansible$ cat setup.yml
---
- name: Gather facts
  hosts: all
  tags: always
  tasks:
    - name: Gather facts
      setup:

- name: Enforce every configurations
  hosts: all
  roles:
    -  {  role:  borg,   tags: [ 'borg' ] }
...
```

## Configuration

First of all you only need to configure hosts that are backup clients. There are several `host_vars` you can define to this effect :
- `borg_server`: a string that contains a hostname.
- `borg_jobs`: a list of dict, one item per job with the following keys:
  - `name`: the name of the borg job, an alphanumeric string.
  - `path`: an optional path containing the files to backup.
  - `command_to_pipe`: an optional command to pipe the backup data from.
  - `pre_command`: an optional command to run before a job.
  - `post_command`: an optional command to run after a job.
  - `exclude`: an optional list of paths containing locations to exclude.
- `borg_prune_arguments`: a string passed to the `borg prune` command, defaults to `'--keep-within 30d'` for a 30 days backups retention.

To be valid a borg job entry needs to have a name and exactly one of `path` or `command_to_pipe` key.

## Jobs examples

Here are some job examples :
- backup a simple path, exclude a subdirectory :
  ```yaml
  - { name: etc, path: "/etc", exclude: [ "/etc/firmware" ] }
  ```
- backup from a command output, this is what I use in conjunction with another of my yet unreleased roles :
  ```yaml
  - name: mysqldump
    command_to_pipe: >
      /usr/bin/mysqldump -h {{ mysql_server }}
                         -u {{ ansible_hostname }}
                         -p {{ ansible_local.mysql_client.password }}
                         --single-transaction
                         --add-drop-database
                         -B {{ ansible_hostname }}
  ```
- backup job with pre and post commands, what I use for my gitea server on OpenBSD :
  ```yaml
  - name: gitea
    path: "/tmp/gitea.zip"
    pre_command: "echo '/usr/local/sbin/gitea -C /etc/gitea -c /etc/gitea/app.ini dump -f /tmp/gitea.zip' | su -l _gitea"
    post_command: "rm -f /tmp/gitea.zip"
  ```

## What the role does

### On the servers

On servers, the role creates a `borg` user with `/srv/borg` as a home directory where backups will be stored. For each client, a line in the borg user's `authorized_keys` file is generated to enforce and limit access to only one clients' repository.

### On the clients

On clients, the role creates a borg ssh key for the root user and generates a backup script in `/usr/local/bin/adyxax_backup.sh`. The role also adds a cron job that will run the backup script each nigh. Lastly it makes sure the client's borg repository is properly initialised on the server.

### Action plugins

There is an action plugin that validates host_vars types and values for each borg role variable, and another that parses the borg_server entries from all host_vars and set a borg fact for both machines to be backed up and for machines that are specified as backup targets (so that they do not require any manual configuration or variables). This action plugin also enforces the job rules to make sure those are valid and without ambiguities.

### Ansible fact

There is a fact script deployed on each server. It is used to retrieve the ssh public key of clients or the repository status of servers and used in tasks.

## Usefull command:

Manually schedule a backup run :
```sh
ansible all -i hosts -m shell -a "/usr/local/bin/adyxax_backup.sh"
```
