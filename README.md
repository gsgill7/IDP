# Autonomous Automated Guided Vehicle (AGV)

This repository contains the software implementation for a fully autonomous Automated Guided Vehicle (AGV), developed as part of the Cambridge 2nd Year Part IB Integrated Design Project (IDP).

The robot is engineered to navigate a complex topological maze autonomously, perform dynamic line-following, detect and identify colored blocks using sensor fusion, collect items from racks, and deliver them to designated bays. The system features a robust and modular software architecture designed to bridge high-level algorithmic control with low-level hardware constraints.

## Technical Highlights

The codebase is written in MicroPython for the Raspberry Pi Pico (RP2040) and emphasizes a strict separation of concerns across hardware abstraction, kinematics, sensor processing, and high-level control logic.

* **Graph-Based Pathfinding:** Implements Dijkstra's algorithm (`navigation.py`) to compute the shortest path across a predefined topological map of the maze in real-time.
* **Sensor Fusion & Signal Processing:**
  * **Color Classification:** Custom I2C drivers for the TCS34725 sensor (`sensors.py`), calculating color temperature, estimating lux, and normalizing RGB values to accurately classify block colors under varying lighting conditions.
  * **Distance Sensing:** Integration with the VL53L0X Time-of-Flight (ToF) sensor for precise proximity detection of target boxes.
  * **Interrupt-Driven Junction Detection:** Utilizes hardware interrupts on infrared line sensors for immediate, non-blocking junction recognition, enabling precise 90-degree and 180-degree relative turns.
* **Differential Drive & Kinematics:** Implements a closed-loop line-following algorithm using differential steering and customizable correction factors (`robot.py`) to maintain high-speed stability and trajectory correction.
* **Object-Oriented Architecture:** Highly modular design encapsulating actuators, sensors, and the main robot state machine. This architectural decision facilitated rapid iteration and seamless integration of complex subsystems.

## Repository Structure

* `main.py`: Entry point and high-level mission control sequence.
* `robot.py`: Core `Robot` class encapsulating the state machine, line-following logic, and junction handling.
* `navigation.py`: Topological maze mapping, relative turn calculations, and Dijkstra's shortest path algorithm.
* `sensors.py`: Hardware abstraction layer and drivers for the TCS34725 (Color) and VL53L0X (ToF) sensors.
* `actuators.py`: PWM control classes for DC motors and servos.
* `libs/`: External dependencies and vendor libraries.

## Hardware Stack

* **Microcontroller:** Raspberry Pi Pico (RP2040)
* **Sensors:** 
  * TCS34725 (RGB Color Sensor)
  * VL53L0X (Time-of-Flight Distance Sensor)
  * Infrared Line Tracking Sensors
* **Actuators:** DC Motors with PWM speed control, Servo Motors
