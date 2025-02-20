You control a robot capable of building structures by moving and manipulating blocks in a 4x3 grid environment with a maximum height of 3.

The robot can perform various actions such as moving horizontally at the same height, moving up or down to adjacent heights, placing or removing blocks at neighboring positions, and creating or destroying blocks at the depot.

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
- There are successor relationships between the numbers n0, n1, n2, and n3, indicating the possible heights.

Your goal is to achieve the following configuration:
- The height at pos-1-2 needs to be 3.
- All other positions must remain at height 0.
- The robot should not have a block at the end of the task.