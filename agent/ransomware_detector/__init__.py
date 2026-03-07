"""
Ransomware Terminator — Path 2 MVP

Detects ransomware-like behaviour by monitoring:
- File entropy (encrypted files have entropy ≈ 8.0 bits/byte)
- Disk I/O patterns (sudden write spikes)
- Process behaviour (mass file renames, suspicious extensions)

Safety: AUTO_REMEDIATION_ENABLED defaults to false. All kill actions
default to dry_run=True.
"""
