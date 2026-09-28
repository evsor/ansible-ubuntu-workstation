# ansible-ubuntu-workstation

Bootstrap an Ubuntu workstation with Ansible with multiple profiles support

## Setup

Install Ansible:

```bash
./install.sh
```

Choose profile:

```bash
cp profile.yml.example profile.yml   # set to personal or work
```

`profile.yml` is gitignored. You can also pass `-e profile=work` instead

## Usage

```bash
# with profile.ylm present
ansible-playbook main.yml --ask-become-pass

# dry-run
ansible-playbook main.yml --check --diff --ask-become-pass

# remove everything, except user data
ansible-playbook main.yml --ask-become-pass -e workstation_state=absent

# remove everything + user data
ansible-playbook main.yml --ask-become-pass -e workstation_state=absent -e remove_user_data=true

# include separate roles
ansible-playbook main.yml --ask-become-pass -e '{"workstation_roles":["tools"]}'
```

## Adding and removing software

Software is defined in the catalogs(var files):

| Role | Catalog | Contents |
| --- | --- | --- |
| `base` | [roles/base/vars/main.yml](roles/base/vars/main.yml) | desktop apps, system packages, snaps, apt repos, `.deb` releases |
| `tools` | [roles/tools/vars/main.yml](roles/tools/vars/main.yml) | CLI tooling: apt repos and packages, GitHub release binaries and tarballs, Helm repos and plugins |
| `dotfiles` | — | clones the dotfiles repo and runs `stow` |

To add a package, add a line to the list. To uninstall, mark the line as `absent`. Delete the line after run.

### Per-profile state

An entry is installed on every profile unless `profiles` is defined. The states are `present`, `absent` and `ignore`:

```yaml
  - { name: htop }                                   # present everywhere
  - { name: slack, profiles: { personal: absent } }  # work only, removed from personal
  - { name: steam, profiles: { work: ignore } }      # personal only, work ignored
  - { name: cache, user_data: true }                 # removed only with -e remove_user_data=true
```
