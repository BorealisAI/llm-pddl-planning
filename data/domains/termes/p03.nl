You control a robot capable of building structures by moving and manipulating blocks in a 4x3 grid environment with a maximum height of 4.

The robot can perform several actions:
- Move horizontally at the same height.
- Move vertically up or down by one height level.
- Place a block at a neighboring position if it has a block and the heights match.
- Remove a block at a neighboring position if it does not have a block and the heights match.
- Create a block at the depot, which results in the robot holding the block.
- Destroy a block at the depot if the robot is holding a block.

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
- There are successor relationships between the numbers n0 to n4, indicating increasing heights.

Your goal is to achieve the following configuration:
- The height at pos-3-1 needs to be 4.
- All other positions must remain at height 0.
- The robot should not have a block at the end of the task.