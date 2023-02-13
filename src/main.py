"""!
@file main.py
    This file contains a program that uses a proportional controller to
    control a motors position, and sends that data over a UART communication
    to be plotted by a c-python program. This is implemented as a series of
    tasks.

@author Tristan de Lemos, Trenten Spicer, Rees Verleur
@date   2022-Feb-13  
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
    """!@brief Task which runs the proportional controller to control the motor.
    @details This task runs the proportional controller and puts position data in
        the queue so that another task can take the data out and send it over the
        serial port to the c-python program which plots the step response

    @param shares A list holding the share and queue used by this task
    """
    # Get references to the share and queue which have been passed to this task
    my_share, my_queue = shares
    # Read encoder to get an initial value
    read = enc.read()
    # Zero the position so that the step response moves a known amount
    pos = 0
    # Record the start time for later use in plotting
    start = utime.ticks_ms()
    # Run for all time
    while True:
        # Update the read and postion values
        read,pos = enc.update(read,pos)
        # Calculate the current time
        time = (utime.ticks_diff(utime.ticks_ms(),start))
        # Create function string and put in queue as bytes
        for x in (bytes(f"{time},{pos}\r\n",'ascii')):
            my_queue.put(x)
        # Calculate effort with pos and neg limits
        effort = con.run(pos)
        if effort<-100:
            effort = -100
        elif effort>100:
            effort = 100
        # Set the motor duty cycle
        motor.set_duty_cycle(effort)
        # Yield and come back at top of while loop in next call
        yield
        
def task2_fun(shares):
    """!@brief Task which takes data out of queue and sends it over UART
    @details This task takes the data out of the queue and sends it over uart
        to the c-python program for plotting. This runs at a much lower frequency
        than the motor controller so that the entire step response data can be sent
        and plotted at once
    @param shares A tuple of a share and queue from which this task gets data
    """
    # Get references to the share and queue which have been passed to this task
    the_share, the_queue = shares
    # Run for all time
    while True:
        # While there is stuff in the queue
        while q0.any():
            # Take it out, interpret it as a byte and send it over uart
            x = the_queue.get().to_bytes(1,'big')
            u2.write(x)
        # Once there is nothing left the step response is done tag the end so the c-python program knows
        u2.write(b'done\r\n')
        yield
        
#def task3_fun(shares):
#    """!@brief Task which runs the proportional controller to control the motor.
#    @details This task runs the proportional controller and puts position data in
#        the queue so that another task can take the data out and send it over the
#        serial port to the c-python program which plots the step response
#
#    @param shares A list holding the share and queue used by this task
#    """
#    # Get references to the share and queue which have been passed to this task
#    my_share, my_queue = shares
#    # Read encoder to get an initial value
#    read = enc.read()
#    # Zero the position so that the step response moves a known amount
#   pos = 0
#   # Record the start time for later use in plotting
#   start = utime.ticks_ms()
#   # Run for all time
#    while True:
#       # Update the read and postion values
#       read,pos = enc.update(read,pos)
#       # Calculate the current time
#       time = (utime.ticks_diff(utime.ticks_ms(),start))
#       # Create function string and put in queue as bytes
#       for x in (bytes(f"{time},{pos}\r\n",'ascii')):
#           my_queue.put(x)
#       # Calculate effort with pos and neg limits
#       effort = con.run(pos)
#        if effort<-100:
#           effort = -100
#        elif effort>100:
#            effort = 100
#        # Set the motor duty cycle
#        motor.set_duty_cycle(effort)
#        # Yield and come back at top of while loop in next call
#        yield
        
if __name__ == "__main__":
    
    # Initialize uart communication
    u2 = pyb.UART(2, baudrate=115200, timeout = 65383)
    # Initialize encoder object
    enc = EncoderDriver(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    # Initialize motor object
    motor = MotorDriver (pyb.Pin.board.PA10,pyb.Pin.board.PB4,pyb.Pin.board.PB5,3)
    # Initialize proportional controller with default values
    con = ProControl()
    # Wait for c-python program to send setpoint and gain (blocking code so not in task)
    con.set_setpoint(int(u2.readline()))
    con.set_Kp(float(u2.readline()))
    
    # Create a share and a queue to pass data between tasks
    share0 = task_share.Share('B', thread_protect=False, name="Share 0")
    q0 = task_share.Queue('B', 4000, thread_protect=False, overwrite=False,
                          name="Queue 0")
    share1 = task_share.Share('B',thread_protect=False, name="Share 1")
    q1 = task_share.Queue('B', 4000, thread_protect=False, overwrite=False,
                          name="Queue 1")

    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    task1 = cotask.Task(task1_fun, name="Task_1", priority=3, period=20,
                        profile=False, trace=False, shares=(share0, q0))
    task2 = cotask.Task(task2_fun, name="Task_2", priority=1, period=1000,
                        profile=False, trace=False, shares=(share0, q0))
    #task3 = cotask.Task(task3_fun, name="Task_3", priority=2, period=20,
    #                    profile=False, trace=False, shares=(share1, q1))
    #task4 = cotask.Task(task4_fun, name="Task_4", priority=0, period=1000,
    #                    profile=False, trace=False, shares=(share1, q1))
    cotask.task_list.append(task1)
    cotask.task_list.append(task2)
    #cotask.task_list.append(task3)
    #cotask.task_list.append(task4)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect()

    # Run the scheduler with the chosen scheduling algorithm. Quit if ^C pressed
    while True:
        try:
            cotask.task_list.pri_sched()
        except KeyboardInterrupt:
            motor.set_duty_cycle(0)
            break

