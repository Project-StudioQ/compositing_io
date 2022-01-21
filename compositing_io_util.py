# ----------------------------------------------------------------------------------------------------
# Public Functions
# ----------------------------------------------------------------------------------------------------

# -- Check --

def can_substitute_type(val):
    """ そのまま代入出来る型か？

    Args:
        val (Object): 任意の値

    Returns:
        bool: True = Yes, False = No
    """
    if type(val) is str or type(val) is int or type(val) is float or type(val) is bool:
        return True
    else:
        return False