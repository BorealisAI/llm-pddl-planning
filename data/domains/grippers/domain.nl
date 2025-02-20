The gripper domain involves a world with multiple rooms, robots, and objects (balls). Each robot has two grippers that can be used to pick up and drop objects. The goal is to move objects from their initial locations to the desired goal locations using the robots and their grippers.

The domain includes three actions:

1. move: This action allows a robot to move from one room to another. The precondition is that the robot must be in the starting room. The effect is that the robot is no longer in the starting room and is now in the destination room.

2. pick: This action allows a robot to pick up an object using one of its grippers. The preconditions are that the object and the robot must be in the same room, and the specified gripper must be free (not holding any object). The effect is that the robot is now carrying the object with the specified gripper, the object is no longer in the room, and the gripper is no longer free.

3. drop: This action allows a robot to drop an object it is carrying in a specific room using one of its grippers. The preconditions are that the robot must be carrying the object with the specified gripper and the robot must be in the specified room. The effect is that the object is now in the room, the gripper is free, and the robot is no longer carrying the object with that gripper.
