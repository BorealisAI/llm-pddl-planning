def describe_predicate(predicate_name, predicate_args):
    """
    Predicates:
    - (height ?p - position ?h - numb)
    - (at ?p - position)
    - (has-block)
    - (SUCC ?n1 - numb ?n2 - numb)
    - (NEIGHBOR ?p1 - position ?p2 - position)
    - (IS-DEPOT ?p - position)

    :param predicate_name: str
    :param predicate_args: Tuple[str]
    :return: Tuple[str, str] - (positive, negative)
    """
    # (height ?p - position ?h - numb)
    if predicate_name == "height":
        p, h = predicate_args
        return f"The height at position {p} is {h}.", f"The height at position {p} is not {h}."
    # (at ?p - position)
    elif predicate_name == "at":
        (p,) = predicate_args
        return f"The robot is at position {p}.", f"The robot is not at position {p}."
    # (has-block)
    elif predicate_name == "has-block":
        return "The robot has a block.", "The robot does not have a block."
    # (SUCC ?n1 - numb ?n2 - numb)
    elif predicate_name == "SUCC":
        n1, n2 = predicate_args
        return f"{n2} is the successor of {n1}.", f"{n2} is not the successor of {n1}."
    # (NEIGHBOR ?p1 - position ?p2 - position)
    elif predicate_name == "NEIGHBOR":
        p1, p2 = predicate_args
        return f"Position {p1} is a neighbor of position {p2}.", f"Position {p1} is not a neighbor of position {p2}."
    # (IS-DEPOT ?p - position)
    elif predicate_name == "IS-DEPOT":
        (p,) = predicate_args
        return f"Position {p} is the depot.", f"Position {p} is not the depot."
    else:
        raise ValueError(f"Unknown predicate: {predicate_name}")