# Telegram Bot with NoSQL Redis

## Overview
This repository contains a Telegram bot that utilizes Redis for data storage.

## Requirements
- Python 3.x
- Redis

## Installation
1. Clone the repository.
2. Install required packages: `pip install -r requirements.txt`
3. Edit `settings.py` to configure bot settings.
4. Run the bot: `python main.py`

## Features
- Task Management
  - Add Task: Add tasks with name, details, priority, and due date.
  - List Tasks: View the list of added tasks.
  - Delete Task: Delete specific tasks.
  - Reset Tasks: Delete all saved tasks.

- Place Management
  - Add Place: Add places with name, address, or location coordinates.
  - List Places: View the list of added places.
  - Delete Place: Delete specific places.
  - Reset Places: Delete all saved places.

- General Commands
  - Start/Help: Get information about the bot's commands.

## Usage
Examples of basic commands:
- To add a task: `/addtask Buy groceries | Details: Milk, eggs, bread | Priority: High | Due: 2023-08-31`
- To list tasks: `/listtasks`
- To delete a task: `/deletetask TaskID`
- To reset tasks: `/resettasks`
