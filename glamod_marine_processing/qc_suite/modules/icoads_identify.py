"""Module containing main QC functions which could be applied on a DataBundle."""

from __future__ import annotations

from .qc import failed, passed

# This should be the raw structure.
# In general, I think, we do not need to set qc flags, we just return them (no self.set_qc)
# I hop I did not forget anything.


def is_in_valid_list(
    value: str | int | float, valid_list: str | int | float | list
) -> int:
    """Identify whether a value is in a valid_list.

    Parameters
    ----------
    value : str or int or float
        Value to test
    valid_list : list
         List of valid values

    Returns
    -------
    int
        Return 0 if value is in valid list and 1 otherwise
    """
    if not isinstance(valid_list, list):
        valid_list = [valid_list]
    if value in valid_list:
        return passed
    return failed


def is_buoy(platform_type: int, valid_list: list | int = [6, 7]) -> int:
    """
    Identify whether report is from a moored or drifting buoy based on ICOADS platform type PT.

    Parameters
    ----------
    platform_type : int
        Platform type
    valid_list: list or int
        List of valid platform types

    Returns
    -------
    int
        Return 0 if observation is from a drifting or moored buoy and 1 otherwise
    """
    # I think we should use the CDM platform table?
    # https://glamod.github.io/cdm-obs-documentation/tables/code_tables/platform_type/platform_type.html
    return is_in_valid_list(platform_type, valid_list)


def is_drifter(platform_type: int, valid_list: list | int = 7) -> int:
    """
    Identify whether report is from a drifting buoy based on ICOADS platform type PT.
    trackqc is only applied to drifting buoys. Used to filter drifting buoys.

    Parameters
    ----------
    platform_type : int
        Platform type
    valid_list: list or int
        List of valid platform types

    Returns
    -------
    int
        Return 0 if observation is from a drifting buoy and 1 otherwise
    """
    return is_in_valid_list(platform_type, valid_list)


def is_ship(
    platform_type: int, valid_list: list | int = [0, 1, 2, 3, 4, 5, 10, 11, 12, 17]
) -> int:
    """
    Identify whether report is from a ship based on ICOADS platform type PT.
    Marien Air Temperature QC only performed on reports from ships. Used to filter ships.

    Parameters
    ----------
    platform_type : int
        Platform type
    valid_list: list or str
        List of valid platform types

    Returns
    -------
    int
        Return 0 if observation is from a ship and 1 otherwise
    """
    # I think we should use the CDM platform table?
    # https://glamod.github.io/cdm-obs-documentation/tables/code_tables/platform_type/platform_type.html
    return is_in_valid_list(platform_type, valid_list)


def is_deck(dck: int, valid_list: list | int = 780) -> int:
    """
    Identify obs that are from ICOADS Deck 780 which consists of obs from WOD.
    Observations from deck 780 are not used so they are not included in QC.

    Parameters
    ----------
    dck : int
        Deck of observation
    valid_list: list or int
        List of valid deck numbers

    Returns
    -------
    int
        return 0 if observation is in deck 780 and 1 otherwise
    """
    # Do we need this function?
    # Where/Why do we need "is780"?
    # I think this function should return a boolean value, isn't it?
    # We do not have this information explicitly in the CDM.
    return is_in_valid_list(dck, valid_list)
