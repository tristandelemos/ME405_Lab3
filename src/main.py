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
import random



def task1_fun():
    """!@brief Task which runs the proportional controller to control the motor.
    @details This task runs the proportional controller and sends position data over
        UART to a C-Python program which plots the data

    """
    # Read encoder to get an initial value
    read_1 = enc_1.read()
    # Zero the position so that the step response moves a known amount
    pos_1 = 0
    # Record the start time for later use in plotting
    start_1 = utime.ticks_ms()
    # Run for all time
    while True:
        # Update the read and postion values
        read_1,pos_1 = enc_1.update(read_1,pos_1)
        # Calculate the current time
        time_1 = (utime.ticks_diff(utime.ticks_ms(),start_1))
        # Create function string and put in queue as bytes
        u2.write(f"motor 1,{time_1},{pos_1}\r\n")
        # Calculate effort with pos and neg limits
        effort_1 = con_1.run(pos_1)
        if effort_1<-100:
            effort_1 = -100
        elif effort_1>100:
            effort_1 = 100
        # Set the motor duty cycle
        motor_1.set_duty_cycle(effort_1)
        # Yield and come back at top of while loop in next call
        yield
        
def task2_fun():
    """!@brief Task which runs the proportional controller to control the motor.
    @details This task runs the proportional controller and sends position data over
        UART to a C-Python program which plots the data

    """
    # Read encoder to get an initial value
    read_2 = enc_2.read()
    # Zero the position so that the step response moves a known amount
    pos_2 = 0
    # Record the start time for later use in plotting
    start_2 = utime.ticks_ms()
    # Run for all time
    while True:
        # Update the read and postion values
        read_2,pos_2 = enc_2.update(read_2,pos_2)
        # Calculate the current time
        time_2 = (utime.ticks_diff(utime.ticks_ms(),start_2))
        # Create function string and put in queue as bytes
        u2.write(f"motor 2,{time_2},{pos_2}\r\n")
        # Calculate effort with pos and neg limits
        effort_2 = con_2.run(pos_2)
        if effort_2<-100:
            effort_2 = -100
        elif effort_2>100:
            effort_2 = 100
        # Set the motor duty cycle
        motor_2.set_duty_cycle(effort_2)
        # Yield and come back at top of while loop in next call
        yield
        
def main():
    """!@brief This is a test program for the motor drivers
        @details The program uses the random module to set
            the position and gains (within certain ranges)
            of both motors every few seconds. 
    """
    while True:
        # Keep running on current gains/setpoints for 5000 cycles.
        #This is enough that the motor positions can be played with by hand to inspect the performance
        for n in range(0,5000):
            try:
                cotask.task_list.pri_sched()
            except KeyboardInterrupt:
                # If there is a keyboard interrupt, turn off the motors
                motor_1.set_duty_cycle(0)
                motor_2.set_duty_cycle(0)
                # Tell the C-Python program that we are done
                u2.write(b'end\r\n')
                # Print exit statement
                print('Program exited by user')
                # Raise exception to exit out of all loops
                raise Exception('Program Exited by User')
                break
        # With seperate 50% chances change the motor setpoints and gains
        if random.randint(0,1):
            con_1.set_setpoint(random.randint(0,4096))
        if random.randint(0,1):
            con_2.set_setpoint(random.randint(0,4096))
        if random.randint(0,1):
            con_1.set_Kp(random.uniform(0,0.15))
        if random.randint(0,1):
            con_2.set_Kp(random.uniform(0,0.15))
            
    motor_1.set_duty_cycle(0)
    motor_2.set_duty_cycle(0)
     
if __name__ == "__main__":
    """!@brief This script creates instances of all the required modules and
            calls the test program in main()
        @details The classes have to be instantiated here outside of functions
            so that their values can be accessed and changed by any function.
            This script also waits for the C-python program to be started before
            calling the test program and starting the control loops
        
    """
    
    # Initialize uart communication
    u2 = pyb.UART(2, baudrate=115200, timeout = 65383)
    # Initialize encoder objects
    enc_1 = EncoderDriver(pyb.Pin.board.PB6, pyb.Pin.board.PB7, 4)
    enc_2 = EncoderDriver(pyb.Pin.board.PC6, pyb.Pin.board.PC7, 8)
    # Initialize motor objects
    motor_1 = MotorDriver (pyb.Pin.board.PA10,pyb.Pin.board.PB4,pyb.Pin.board.PB5,3)
    motor_2 = MotorDriver (pyb.Pin.board.PC1,pyb.Pin.board.PA0,pyb.Pin.board.PA1,5)
    # Initialize proportional controllers with default values
    con_1 = ProControl()
    con_2 = ProControl()
    # Set initial setpoints and gains for motors
    con_1.set_setpoint(1024)
    con_1.set_Kp(0.15)
    con_2.set_setpoint(2048)
    con_2.set_Kp(0.05)
    
    # Wait for C-Python program to be ready
    start = u2.readline()
    if start != b'ready\r\n':
        raise Exception('C-python program needs to be started after this program')

    # Create the tasks. If trace is enabled for any task, memory will be
    # allocated for state transition tracing, and the application will run out
    # of memory after a while and quit. Therefore, use tracing only for 
    # debugging and set trace to False when it's not needed
    task1 = cotask.Task(task1_fun, name="Task_1", priority=1, period=20,
                        profile=False, trace=False)
    task2 = cotask.Task(task2_fun, name="Task_2", priority=1, period=20,
                        profile=False, trace=False)
    cotask.task_list.append(task1)
    cotask.task_list.append(task2)

    # Run the memory garbage collector to ensure memory is as defragmented as
    # possible before the real-time scheduler is started
    gc.collect()
    # Run the test program in main()
    main()
    # Run the scheduler with the chosen scheduling algorithm. Quit if ^C pressed
    
        

