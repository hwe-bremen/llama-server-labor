"""Read-only physical counters via the macOS IORegistry tree. No disk I/O workload."""
from pathlib import Path
import re
import subprocess
import time


def inventory():
    raw = subprocess.check_output(['/usr/sbin/ioreg', '-r', '-c', 'IOBlockStorageDriver',
                                   '-l', '-w', '0'], timeout=15).decode('utf-8', 'replace')
    nodes, stack = [], []
    for line in raw.splitlines():
        if '+-o ' in line:
            depth = line.index('+-o ')
            while stack and stack[-1]['depth'] >= depth:
                stack.pop()
            match = re.search(r'\+-o (.*?)  <class ([^,]+), id ([^,]+),', line)
            if not match:
                raise RuntimeError('Unbekanntes IORegistry-Knotenformat')
            n = {'depth': depth, 'name': match[1], 'class': match[2], 'registry_id': match[3],
                 'ancestors': stack.copy()}
            nodes.append(n); stack.append(n)
        if not stack:
            continue
        n = stack[-1]
        bsd = re.search(r'"BSD Name" = "([^"]+)"', line)
        if bsd:
            n['bsd'] = bsd[1]
        if '"Whole" = Yes' in line:
            n['whole'] = True
        if n['class'] == 'IOBlockStorageDriver' and '"Statistics" =' in line:
            for key, label in [('read_bytes', 'Bytes (Read)'), ('read_ops', 'Operations (Read)'),
                               ('write_bytes', 'Bytes (Write)')]:
                match = re.search('"' + re.escape(label) + r'"=(\d+)', line)
                if match:
                    n[key] = int(match[1])
    return raw, nodes


def volume_device(path):
    out = subprocess.check_output(['/bin/df', '-k', str(path)], text=True, timeout=10)
    device = out.splitlines()[1].split()[0]
    if not device.startswith('/dev/'):
        raise RuntimeError('Volume nicht als BSD-Gerät zugeordnet')
    return device[5:]


def snapshot():
    start = time.time()
    raw, nodes = inventory()
    mount = Path('/Volumes/Extern M4 Speicher')
    if not mount.is_mount() or mount.is_symlink():
        raise RuntimeError('Samsung-T7-Volume fehlt')
    result = {'start_epoch': start, 'devices': {}}
    for label, path in [('internal', Path(__file__).resolve().parent), ('external', mount)]:
        bsd = volume_device(path)
        found = [n for n in nodes if n.get('bsd') == bsd]
        if len(found) != 1:
            raise RuntimeError('Volume-IORegistry-Zuordnung nicht eindeutig: ' + bsd)
        chain = found[0]['ancestors'] + [found[0]]
        # AppleAPFSMedia also declares Whole=Yes, but represents a synthesized
        # container, not the physical IOMedia below IOBlockStorageDriver.
        whole = [n for n in chain if n.get('whole') and n['class'] == 'IOMedia']
        drivers = [n for n in chain if n['class'] == 'IOBlockStorageDriver']
        if len(whole) != 1 or len(drivers) != 1:
            raise RuntimeError('Physische Volume-Zuordnung nicht eindeutig: ' + bsd)
        driver = drivers[0]
        if any(k not in driver for k in ('read_bytes', 'read_ops', 'write_bytes')):
            raise RuntimeError('Physische Lesezähler nicht verfügbar')
        if label == 'external' and not all(x in whole[0]['name'].lower() for x in ('samsung', 't7')):
            raise RuntimeError('Externes Volume nicht als Samsung T7 identifiziert')
        result['devices'][label] = {'volume_bsd': bsd, 'physical_bsd': whole[0]['bsd'],
            'media': whole[0]['name'], 'registry_id': driver['registry_id'],
            **{k: driver[k] for k in ('read_bytes', 'read_ops', 'write_bytes')}}
    result['end_epoch'] = time.time()
    return result


def delta(before, after):
    out = {}
    for label in ('internal', 'external'):
        a, b = before['devices'][label], after['devices'][label]
        for key in ('volume_bsd', 'physical_bsd', 'registry_id', 'media'):
            if a[key] != b[key]:
                raise RuntimeError('Datenträgeridentität während Messfenster geändert')
        out[label] = {k: b[k] - a[k] for k in ('read_bytes', 'read_ops', 'write_bytes')}
        if any(v < 0 for v in out[label].values()):
            raise RuntimeError('Datenträgerzähler zurückgesetzt')
    return out


if __name__ == '__main__':
    import json
    print(json.dumps(snapshot(), indent=2))
