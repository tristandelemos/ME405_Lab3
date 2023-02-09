"""!
@file basic_tasks.py
    This file contains a demonstration program that runs some tasks, an
    inter-task shared variable, and a queue. The tasks don't really @b do
    anything; the example just shows how these elements are created and run.

@author JR Ridgely
@date   2021-Dec-15 JRR Created from the remains of previous example
@copyright (c) 2015-2021 by JR Ridgely and released under the GNU
    Public License, Version 2. 
"""

import gc
import pyb
import cotask
import task_share
from encoder_driver import EncoderDriver
from motor_driver import MotorDriver
from pro_control import ProControl
import utime



def task1_fun(shares):
    """!
    Task which puts things into a share and a queue.
    @param shares A list holding the share and queue used by this task
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares
    u2 = pyb.UART(2, baudrate=115200, timeout = 65383)
    enc = EncoderDriver(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    motor = MotorDriver (pyb.Pin.board.PA10,pyb.Pin.board.PB4,pyb.Pin.board.PB5,3)
    con = ProControl()
    read = enc.read()
    pos = 0
    
    con.set_setpoint(int(u2.readline()))
    con.set_Kp(float(u2.readline()))
    
    read = enc.read()
    pos = 0
    start = utime.ticks_ms()
    #time = []
    #position = []
    print('Task 1')
        
    #counter = 0
    #while True:
    #    my_share.put(counter)
    #    my_queue.put(counter)
    #    counter += 1

    #    yield 0


    while True:
        
        #con.set_Kp(float(input('Enter gain: ')))
        
        read,pos = enc.update(read,pos)
        #position.append(pos)
        time = (utime.ticks_diff(utime.ticks_ms(),start))
        for x in (f"{time},{pos}\r\n".encode()):
            my_queue.put(x)
        #my_queue.put(f"{time},{pos}\r\n")
        effort = con.run(pos)
        
        if effort<-100:
            effort = -100
        elif effort>100:
            effort = 100
                
        motor.set_duty_cycle(effort)
        yield
    #motor.set_duty_cycle(0) 
    #for x,y in zip(time,position):
    #    u2.write(f"{x},{y}\r\n")
    #    
    #u2.write(b'done\r\n')

def task2_fun(shares):
    """!
    Task which takes things out of a queue and share and displays them.
    @param shares A tuple of a share and queue from which this task gets data
    """
    # Get references to the share and queue which have been passed to this task
    the_share, the_queue = shares
    
    while True:
        for x in the_queue:
            u2.write(x)
            
        u2.write(b'done\r\n')
        yield

    #while True:
    #    # Show everything currently in the queue and the value in the share
    #    print(f"Share: {the_share.get ()}, Queue: ", end='')
    #    while q0.any():
    #        print(f"{the_queue.get ()} ", end='')
    #    print('')#

    #    yield 0


# This code creates a share, a queue, and two tasks, then starts the tasks. The
# tasks run until somebody presses ENTER, at which time the scheduler stops and
# printouts show diagnostic information about the tasks, share, and queue.
if __name__ == "__main__":
    
    

    # Create a share and a queue to test function and diagnostic printouts
    share0 = task_share.Share('b', thread_protect=False, name="Share 0")
    q0 = task_share.Queue('b', 4000, thread_protect=False, overwrite=False,
                          name="Queue 0")

    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    task1 = cotask.Task(task1_fun, name="Task_1", priority=2, period=10,
                        profile=False, trace=False, shares=(share0, q0))
    task2 = cotask.Task(task2_fun, name="Task_2", priority=1, period=2500,
                        profile=False, trace=False, shares=(share0, q0))
    cotask.task_list.append(task1)
    cotask.task_list.append(task2)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect()

    # Run the scheduler with the chosen scheduling algorithm. Quit if ^C pressed
    while True:
        try:
            cotask.task_list.pri_sched()
        except KeyboardInterrupt:
            break

    # Print a table of task data and a table of shared information data
    #print('\n' + str (cotask.task_list))
    #print(task_share.show_all())
    #print(task1.get_trace())
    #print('')
