def describe_predicate(predicate_name, predicate_args):
    """
    Predicates:
    - (clear ?x)
    - (on-table ?x)
    - (arm-empty)
    - (holding ?x)
    - (on ?x ?y)

    :param predicate_name: str
    :param predicate_args: Tuple[str]
    :return: Tuple[str, str] - (positive, negative)
    """
    # (clear ?x)
    if predicate_name == "clear":
        (x,) = predicate_args
        return f"Block {x} is clear.", f"Block {x} is not clear."
    # (on-table ?x)
    elif predicate_name == "on-table":
        (x,) = predicate_args
        return f"Block {x} is on the table.", f"Block {x} is not on the table."
    # (arm-empty)
    elif predicate_name == "arm-empty":
        return "Arm is empty.", "Arm is not empty."
    # (holding ?x)
    elif predicate_name == "holding":
        (x,) = predicate_args
        return f"Arm is holding block {x}.", f"Arm is not holding block {x}."
    # (on ?x ?y)
    elif predicate_name == "on":
        (x, y) = predicate_args
        return f"Block {x} is on block {y}.", f"Block {x} is not on block {y}."
    else:
        raise ValueError(f"Unknown predicate: {predicate_name}")
