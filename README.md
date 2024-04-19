# Risk-Visualizer

# Risk Analysis Dashboard Applications

## Overview
These Python applications are designed as Dash web-based dashboards for analyzing risk factors in various scenarios, allowing users to upload data and visually interact with risk assessments. The applications use Plotly for graphical representations, and Dash with Bootstrap components for the user interface.

---

## Application 1: Risk Analysis with Dynamic Charts and Mitigation Strategies

### Intent
This application enables users to upload Excel files containing data about risk drivers and their sub-components. Users can adjust sliders to rank the importance of each sub-risk driver relative to one another. The application then calculates and displays a priority vector and risk index through bar and pie charts, highlighting the most important sub-risk driver and suggesting mitigation strategies.

### How to Run
1. Install required libraries: `pip install dash dash-bootstrap-components plotly pandas numpy`
2. Run the script: `python <filename>.py`
3. Access the web interface through the local server address provided (usually `http://127.0.0.1:8050/`).
4. Use the "Upload File" button to load your data.
5. Adjust the sliders as necessary and click "Render" to generate the charts and suggested strategies.

### Features
- Upload Excel files for input.
- Dynamic sliders for sub-risk drivers.
- Bar and pie charts to visualize risk indices and priority vectors.
- Display of mitigation strategies for the highest priority risks.

---

## Application 2: Simple Risk Index Analysis Dashboard

### Intent
The second application focuses on allowing users to upload an Excel file and enter risk statuses manually for each listed sub-risk driver. Based on predefined thresholds, it evaluates the risk index and categorizes the sub-risk drivers into different risk levels, which are then visually represented through a bar chart.

### How to Run
1. Install required libraries: `pip install dash dash-bootstrap-components plotly pandas`
2. Run the script: `python <filename>.py`
3. Access the web interface via the local server address provided.
4. Upload the relevant Excel file and input the current status for each risk driver.
5. Click "Analyze Risk" to view the bar chart and a summary of risk categories.

### Features
- Excel file input for defining risk drivers and thresholds.
- Manual input of current status for risk evaluation.
- Bar chart to visualize the risk levels of sub-risk drivers.
- Text summary of risk levels based on the analysis.

---

**Note:** Ensure that the input Excel files conform to the expected format specified in the applications' instructions for proper functionality.
