You control a robot capable of building structures by moving and manipulating blocks in an environment with a 4x3 grid of positions and heights ranging from 0 to 5.

The robot can move at the same height, move up one height, or move down one height. It can also place or remove a block at a neighboring position, or create or destroy a block at the depot. A block's height increases by one when placed and decreases by one when removed.

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
- There are successor relationships between the numbers n0 to n5, indicating the possible heights.

Your goal is to achieve the following configuration:
- The height at pos-2-1 needs to be 5.
- All other positions must remain at height 0.
- The robot should not have a block at the end of the task.