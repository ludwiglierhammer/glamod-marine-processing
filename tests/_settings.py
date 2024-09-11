from __future__ import annotations


def get_settings(dataset):
    if dataset == "C-RAID_1.2":
        import _settings_CRAID

        return _settings_CRAID
    if dataset == "ICOADS_R3.0.2T":
        import _settings_ICOADS

        return _settings_ICOADS
