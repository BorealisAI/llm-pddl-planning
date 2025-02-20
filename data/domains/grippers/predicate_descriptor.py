def describe_predicate(predicate_name, predicate_args):
    """
    Predicates:
    - (at-robby ?r - robot ?x - room)
    - (at ?o - obj ?x - room)
    - (free ?r - robot ?g - gripper)
    - (carry ?r - robot ?o - obj ?g - gripper)

    :param predicate_name: str
    :param predicate_args: Tuple[str]
    :return: Tuple[str, str] - (positive, negative)
    """
    # (at-robby ?r ?x)
    if predicate_name == "at-robby":
        robot, room = predicate_args
        return f"Robot {robot} is in room {room}.", f"Robot {robot} is not in room {room}."
    # (at ?o ?x)
    elif predicate_name == "at":
        obj, room = predicate_args
        return f"Object {obj} is in room {room}.", f"Object {obj} is not in room {room}."
    # (free ?r ?g)
    elif predicate_name == "free":
        robot, gripper = predicate_args
        return f"Gripper {gripper} of robot {robot} is free.", f"Gripper {gripper} of robot {robot} is not free."
    # (carry ?r ?o ?g)
    elif predicate_name == "carry":
        robot, obj, gripper = predicate_args
        return f"Robot {robot} is carrying object {obj} with gripper {gripper}.", f"Robot {robot} is not carrying object {obj} with gripper {gripper}."
    else:
        raise ValueError(f"Unknown predicate: {predicate_name}")