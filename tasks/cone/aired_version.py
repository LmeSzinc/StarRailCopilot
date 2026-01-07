from tasks.cone.keywords import Cone


def list_cones() -> "list[Cone]":
    dict_cone = {}
    # order by cone_id ascending
    cones = list(reversed(Cone.instances.values()))
    # character specific cone first
    for cone in cones:
        if cone.character_name:
            dict_cone[cone.name] = cone
    # then the rest
    for cone in cones:
        dict_cone[cone.name] = cone

    return list(dict_cone.values())
