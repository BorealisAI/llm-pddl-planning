(define (domain gripper-strips)
  (:requirements :strips :typing)
  (:types room obj robot gripper)
  (:predicates)

  (:action move
    :parameters (?r - robot ?from ?to - room)
    :precondition ()
    :effect ()
  )

  (:action pick
    :parameters (?r - robot ?o - obj ?room - room ?g - gripper)
    :precondition ()
    :effect ()
  )

  (:action drop
    :parameters (?r - robot ?o - obj ?room - room ?g - gripper)
    :precondition ()
    :effect ()
  )
)