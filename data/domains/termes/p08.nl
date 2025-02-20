You control a robot capable of building structures by moving and manipulating blocks within a grid of positions, which can have varying heights up to a maximum of three levels.

The environment consists of a 5x4 grid with positions labeled from pos-0-0 to pos-4-3 and four heights numbered from 0 to 3. The robot can move at the same height, move up by one height, or move down by one height. It can also place or remove a block at a neighboring position, or create or destroy a block at the depot. A block's height increases by one when placed and decreases by one when removed.

Initially:
- All positions on the grid have a height of 0.
- The robot is at position pos-2-0, which is designated as the depot.
- The robot does not have a block.
- The positions have the following neighboring relationships:
  - pos-0-0 neighbors pos-1-0 and pos-0-1
  - pos-0-1 neighbors pos-1-1, pos-0-0, and pos-0-2
  - pos-0-2 neighbors pos-1-2, pos-0-1, and pos-0-3
  - pos-0-3 neighbors pos-1-3 and pos-0-2
  - pos-1-0 neighbors pos-0-0, pos-2-0, and pos-1-1
  - pos-1-1 neighbors pos-0-1, pos-2-1, pos-1-0, and pos-1-2
  - pos-1-2 neighbors pos-0-2, pos-2-2, pos-1-1, and pos-1-3
  - pos-1-3 neighbors pos-0-3, pos-2-3, and pos-1-2
  - pos-2-0 neighbors pos-1-0, pos-3-0, and pos-2-1, and is the depot
  - pos-2-1 neighbors pos-1-1, pos-3-1, pos-2-0, and pos-2-2
  - pos-2-2 neighbors pos-1-2, pos-3-2, pos-2-1, and pos-2-3
  - pos-2-3 neighbors pos-1-3, pos-3-3, and pos-2-2
  - pos-3-0 neighbors pos-2-0, pos-4-0, and pos-3-1
  - pos-3-1 neighbors pos-2-1, pos-4-1, pos-3-0, and pos-3-2
  - pos-3-2 neighbors pos-2-2, pos-4-2, pos-3-1, and pos-3-3
  - pos-3-3 neighbors pos-2-3, pos-4-3, and pos-3-2
  - pos-4-0 neighbors pos-3-0 and pos-4-1
  - pos-4-1 neighbors pos-3-1, pos-4-0, and pos-4-2
  - pos-4-2 neighbors pos-3-2, pos-4-1, and pos-4-3
  - pos-4-3 neighbors pos-3-3 and pos-4-2
- There are successor relationships between the numbers as follows: n1 succeeds n0, n2 succeeds n1, and n3 succeeds n2.

Your goal is to achieve the following configuration:
- The height at pos-0-2 needs to be 3.
- The height at pos-1-1 needs to be 3.
- All other positions must remain at height 0.
- The robot should not have a block at the end of the task.