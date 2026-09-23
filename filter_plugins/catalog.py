"""Decide what state each catalog entry should be in on this workstation.

A catalog entry is present on every profile unless its `profiles` mapping says
otherwise:

    - name: mongodb-mongosh
      profiles: { personal: absent }   # removed on personal, present on work

Per-profile values are `present`, `absent` or `ignore` (leave it alone).

Entries marked `user_data: true` are removed only when remove_user_data is set.

A teardown (workstation state `absent`) turns every managed entry to absent.
"""
from ansible.errors import AnsibleFilterError
from ansible.module_utils.parsing.convert_bool import boolean

STATES = ('present', 'absent', 'ignore')


def _label(entry):
    return entry.get('name') or entry.get('path') or repr(entry)


def _resolve(entry, workstation):
    profiles = entry.get('profiles', {})
    if not isinstance(profiles, dict):
        raise AnsibleFilterError(
            f"{_label(entry)}: 'profiles' must be a mapping such as "
            f"{{personal: absent}}, got {profiles!r}")

    unknown = set(profiles) - set(workstation['profiles'])
    if unknown:
        raise AnsibleFilterError(
            f"{_label(entry)}: unknown profile(s) {sorted(unknown)}, "
            f"expected any of {workstation['profiles']}")

    wanted = profiles.get(workstation['profile'], 'present')
    if wanted not in STATES:
        raise AnsibleFilterError(
            f"{_label(entry)}: state {wanted!r} for profile "
            f"{workstation['profile']!r} must be one of {list(STATES)}")

    if wanted == 'ignore':
        return 'ignore'
    if workstation['state'] == 'absent':
        wanted = 'absent'

    if wanted == 'absent':
        if boolean(entry.get('user_data', False)) and not boolean(workstation['remove_user_data']):
            return 'ignore'
    return wanted


def managed(catalog, workstation, only=None):
    """Entries this run manages, each copied with a resolved `state` key.

    Entries resolving to `ignore` are dropped. Pass `only` ('present' or
    'absent') to keep just that state.
    """
    if only not in (None, 'present', 'absent'):
        raise AnsibleFilterError(f"managed: 'only' must be present or absent, got {only!r}")

    result = []
    for entry in catalog:
        if 'state' in entry:
            raise AnsibleFilterError(
                f"{_label(entry)}: catalog entries must not set 'state', "
                f"use 'profiles' instead")
        state = _resolve(entry, workstation)
        if state == 'ignore' or (only and state != only):
            continue
        result.append({**entry, 'state': state})
    return result


class FilterModule:
    def filters(self):
        return {'managed': managed}
