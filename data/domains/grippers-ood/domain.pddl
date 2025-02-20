(define (domain gripper-strips)
 (:requirements :strips :typing) 
 (:types room obj robot gripper)
 (:predicates (at-robby ?r - robot ?x - room)
 	      (at ?o - obj ?x - room)
	      (free ?r - robot ?g - gripper)
	      (carry ?r - robot ?o - obj ?g - gripper)
	      (prepared ?x - room)
  )
   (:action move
       :parameters  (?r - robot ?from ?to - room)
       :precondition (and  (at-robby ?r ?from) (prepared ?to))
       :effect (and  (at-robby ?r ?to)
             (not (prepared ?to))
		     (not (at-robby ?r ?from))))

   (:action pick
       :parameters (?r - robot ?obj - obj ?room - room ?g - gripper)
       :precondition  (and  (at ?obj ?room) (at-robby ?r ?room) (free ?r ?g))
       :effect (and (carry ?r ?obj ?g)
		    (not (at ?obj ?room)) 
		    (not (free ?r ?g))))

   (:action drop
       :parameters (?r - robot ?obj - obj ?room - room ?g - gripper)
       :precondition  (and  (carry ?r ?obj ?g) (at-robby ?r ?room))
       :effect (and (at ?obj ?room)
		    (free ?r ?g)
		    (not (carry ?r ?obj ?g))))

   (:action prepare-room
    :parameters (?room - room)
    :precondition (and (not (prepared ?room)))
    :effect (prepared ?room))
)
