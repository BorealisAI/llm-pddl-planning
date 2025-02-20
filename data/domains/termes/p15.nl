You control a robot capable of building structures by moving and manipulating blocks in a 4x3 grid environment with a maximum height of 5.

The robot can perform various actions such as moving at the same height, moving up or down one height, placing or removing a block at a neighboring position, and creating or destroying a block at the depot.

Initially:
- All positions on the grid have a height of 0.
- The robot is at position pos-2-0, which is designated as the depot.
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
- pos-0-2 must have a height of 5.
- pos-3-0 must have a height of 3.
- pos-3-2 must have a height of 2.
- All other positions must remain at height 0.
- The robot should not have a block at the end of the task.