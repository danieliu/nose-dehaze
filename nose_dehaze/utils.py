def extract_mock_name(mock_instance):
    """
    Copied directly from python 3.7+ `mock` for py2 usage.

    Builds and returns the full mock name, e.g. `object.func().attribute`

    :param mock_instance: a python Mock instance
    :return: the full mock instance name
    """
    _name_list = [mock_instance._mock_new_name]
    _parent = mock_instance._mock_new_parent
    last = mock_instance

    dot = "."
    if _name_list == ["()"]:
        dot = ""

    while _parent is not None:
        last = _parent

        _name_list.append(_parent._mock_new_name + dot)
        dot = "."
        if _parent._mock_new_name == "()":
            dot = ""

        _parent = _parent._mock_new_parent

    _name_list = list(reversed(_name_list))
    _first = last._mock_name or "mock"
    if len(_name_list) > 1:
        if _name_list[1] not in ("()", "()."):
            _first += "."
    _name_list[0] = _first
    return "".join(_name_list)
