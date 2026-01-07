# MyArm Control Project

This project is designed for controlling Elephant Robotics MyArm M and C series robots. It includes scripts for control, data collection, and utilities.

## Setup

This project uses `uv` for package management and is pinned to Python 3.10.

1.  **Install uv** (if not already installed):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Sync dependencies**:
    ```bash
    uv sync
    ```

3.  **Activate virtual environment**:
    ```bash
    source .venv/bin/activate
    ```

## Project Structure

- `control_scripts/`: Scripts for sending commands to the robots.
- `data_collection/`: Scripts for recording robot state and sensor data.
- `data/`: Storage for collected data (`raw` and `processed`).
- `utils/`: Utility functions.

## Usage

To run a script using the project's environment:
```bash
uv run python control_scripts/your_script.py
```
