(define (domain blocksworld-4ops)
  (:requirements :strips)
  (:predicates)

  (:action pickup
    :parameters (?ob)
    :precondition ()
    :effect ()
  )

  (:action putdown
    :parameters (?ob)
    :precondition ()
    :effect ()
  )

  (:action stack
    :parameters (?ob ?underob)
    :precondition ()
    :effect ()
  )

  (:action unstack
    :parameters (?ob ?underob)
    :precondition ()
    :effect ()
  )
)