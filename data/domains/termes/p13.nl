You control a robot capable of building structures by moving and manipulating blocks in a 4x3 grid environment with a maximum height of 4.

The robot can perform several actions:
- Move horizontally at the same height.
- Move vertically up or down by one height level.
- Place a block at a neighboring position if it has a block and the heights match, except at the depot.
- Remove a block at a neighboring position if it does not have a block and the heights match, except at the depot.
- Create a block at the depot, which the robot will then hold.
- Destroy a block at the depot if the robot is holding a block.

Initially:
- All positions on the grid have a height of 0.
- The robot is at position pos-2-0, which is the depot.
- The robot does not have a block.
- The positions have the following neighboring relationships:
  - pos-0-0 neighbors pos-1-0 and pos-0-1
  - pos-0-1 neighbors pos-1-1, pos-0-0, and pos-0-2
  - pos-0-2 neighbors pos-1-2 and pos-0-1
  - pos-1-0 neighbors pos-0-0, pos-2-0, and pos-1-1
  - pos-1-1 neighbors pos-0-1, pos-2-1, pos-1-0, and pos-1-2
  - pos-1-2 neighbors pos-0-2, pos-2-2, and pos-1-1
  - pos-2-0 neighbors pos-1-0, pos-3-0, and pos-2-1, and is the depot
  - pos-2-1 neighbors pos-1-1, pos-3-1, pos-2-0, and pos-2-2
  - pos-2-2 neighbors pos-1-2, pos-3-2, and pos-2-1
  - pos-3-0 neighbors pos-2-0 and pos-3-1
  - pos-3-1 neighbors pos-2-1, pos-3-0, and pos-3-2
  - pos-3-2 neighbors pos-2-2 and pos-3-1
- There are successor relationships between the numbers n0 to n4, indicating the possible heights.

Your goal is to achieve the following configuration:
- pos-0-1 must have a height of 3.
- pos-2-2 must have a height of 4.
- pos-3-0 must have a height of 3.
- All other positions must have a height of 0.
- The robot should not have a block at the end of the task.