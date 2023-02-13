# ME405_Lab3

In this lab, we learned how to schedule tasks to control multiple motors simultaneously.

When running the program at a period length of 30 milliseconds, the motor plot, shown in Figure 1, becomes degraded and oscillates forever. 
When running the program at period length of 20 milliseconds, shown in Figure 2, the plot ends at a constant value rather than oscillating over it.

Figure 1

![Figure 1](30ms_Step.png)


Figure 2

![Figure 1](20ms_Step.png)


To Do

Rewrite program so no queues and shares are used (send data from same task as motor controller)
Rewrite C-Python program to accept 2 streams of data simultaneously
