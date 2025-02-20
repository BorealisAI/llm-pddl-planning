You control a robot capable of building structures by moving and manipulating blocks in an environment with a 5x4 grid of positions and heights ranging from 0 to 4.

Initially:
- All positions on the 5x4 grid have a height of 0.
- The robot is at position pos-2-0, which is designated as the depot.
- The robot does not have a block.
- The positions have the following neighboring relationships (each position is adjacent to the positions directly north, south, east, and west of it, if such positions exist on the grid):
  - pos-0-0 neighbors pos-1-0 and pos-0-1
  - pos-0-1 neighbors pos-0-0, pos-0-2, and pos-1-1
  - pos-0-2 neighbors pos-0-1, pos-0-3, and pos-1-2
  - pos-0-3 neighbors pos-0-2 and pos-1-3
  - pos-1-0 neighbors pos-0-0, pos-1-1, and pos-2-0
  - pos-1-1 neighbors pos-0-1, pos-1-0, pos-1-2, and pos-2-1
  - pos-1-2 neighbors pos-0-2, pos-1-1, pos-1-3, and pos-2-2
  - pos-1-3 neighbors pos-0-3, pos-1-2, and pos-2-3
  - pos-2-0 neighbors pos-1-0, pos-2-1, and pos-3-0, and is the depot
  - pos-2-1 neighbors pos-1-1, pos-2-0, pos-2-2, and pos-3-1
  - pos-2-2 neighbors pos-1-2, pos-2-1, pos-2-3, and pos-3-2
  - pos-2-3 neighbors pos-1-3, pos-2-2, and pos-3-3
  - pos-3-0 neighbors pos-2-0, pos-3-1, and pos-4-0
  - pos-3-1 neighbors pos-2-1, pos-3-0, pos-3-2, and pos-4-1
  - pos-3-2 neighbors pos-2-2, pos-3-1, pos-3-3, and pos-4-2
  - pos-3-3 neighbors pos-2-3, pos-3-2, and pos-4-3
  - pos-4-0 neighbors pos-3-0 and pos-4-1
  - pos-4-1 neighbors pos-3-1, pos-4-0, and pos-4-2
  - pos-4-2 neighbors pos-3-2, pos-4-1, and pos-4-3
  - pos-4-3 neighbors pos-3-3 and pos-4-2
- There are successor relationships between the numbers n0 to n4, indicating the possible heights of the positions.

Your goal is to achieve the following configuration:
- The height at pos-2-3 must be 4.
- The height at pos-3-0 must be 2.
- All other positions must remain at height 0.
- The robot should not have a block at the end of the task.