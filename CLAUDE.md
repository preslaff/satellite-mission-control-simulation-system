This response summarizes the information related to defining project requirements and details the plan for designing the requested space mission control and simulation application.

### Summary for Designing Agent Guidelines (GEMINI CLI)

The provided sources do not contain explicit information regarding the creation of a guidelines file or configuration for a specific coding agent like GEMINI CLI. However, based on the requirements and the detailed development plan provided in the source material, the core guidelines for any agent tackling this project would focus on the following key areas:

1.  **Project Goal:** Build a comprehensive satellite mission control application capable of high-fidelity orbital simulation and prediction, specifically targeting satellites launched via SpaceX missions.
2.  **Technology Stack Constraints:** Use Python for the backend (specifically FastAPI) and JavaScript/TypeScript with Vite/React for the frontend, utilizing Three.js for $3D$ visualization. Communication must be handled via WebSockets for real-time updates.
3.  **Core Functionality:** Implement real-time satellite tracking using SGP4 propagation from TLE data, manage coordinate system transformations, develop advanced Machine Learning models, and execute $\Delta V$ maneuver optimization/simulation.
4.  **Development Flow:** Start with dedicated Jupyter Notebooks for data exploration, model prototyping, and validating critical core functions (like coordinate systems and orbital mechanics) before integrating them into the backend/frontend framework.

### Planning and Design for the Mission Control Application

The proposed system, named "Satellite Mission Control & Simulation System," is designed to be a comprehensive platform for managing space flights or running high-quality simulations.

#### 1. Core Technology Stack

The application relies on a modern, high-performance stack suitable for real-time data processing and complex calculations:

| Component | Technology | Role/Justification |
| :--- | :--- | :--- |
| **Backend** | Python (FastAPI) | Provides fast performance, automatic API documentation (OpenAPI), native async support, and easy WebSocket integration for ML inference and real-time operations. |
| **Frontend** | JavaScript/TypeScript (Vite + React) | Used for the Mission Control interface. Leverages a rich ecosystem for data visualization and real-time updates. |
| **Visualization** | Three.js / @react-three/fiber | Enables $3D$ visualization of the Earth, satellite orbits, and real-time positions. |
| **Data/ML** | Jupyter, PyTorch/TensorFlow, `skyfield`, `sgp4` | Used for prototyping, training models, and executing high-accuracy coordinate and orbital calculations. |
| **Database** | PostgreSQL + TimescaleDB | Used for persistent storage of satellite data and efficient handling of time-series telemetry data. |

#### 2. Primary Coordinate Systems Feature

The application architecture includes explicit development for handling multiple Primary Coordinate Systems. These systems are crucial for specifying the relative state of a chaser spacecraft ($\vec{F}_c$) relative to a target ($\vec{F}_t$) in space navigation.

The systems planned for implementation include:
*   **ECI (J2000)**
*   **ECEF (WGS84)** transformations
*   **Topocentric (ENU/NED)** systems

The Python library `skyfield` is designated for achieving high-accuracy coordinate transformations.

#### 3. Real Satellite Data and Training Requirements

Acquiring real operational data is challenging due to costs and complexity in space operations. Synthetic datasets and simulation tools like SPIN and SurRender are often used to bridge this gap by generating data for visual-based navigation and pose estimation.

For this application, real data acquisition steps are required to validate models against reality:
*   **Data Sources:** Fetch TLE (Two-Line Element) data from CelesTrak and Space-Track.org, alongside SpaceX launch data from public APIs, and historical satellite telemetry (e.g., Starlink data).
*   **Training Data Needs:** The optimal target dataset size is significant: around $10,000$ satellites $\times 1$ year of tracking data, equating to approximately $87.6$ million data points and $\sim 50$ GB of storage (including raw telemetry).
*   **Features for ML Models:** Inputs must include Position ($\text{x}, \text{y}, \text{z}$) and Velocity ($\text{v}_x, \text{v}_y, \text{v}_z$) in ECI, orbital elements, time of epoch, and environmental factors like solar activity indices ($\text{F}10.7$) and atmospheric density estimates.

#### 4. Satellite Course Correction Simulation

The application will include a **Course Correction Optimizer Model** designed to calculate the optimal $\Delta V$ maneuver sequence.

*   **Model Type:** The **Primary** recommendation is **Reinforcement Learning (RL)**, specifically **Proximal Policy Optimization (PPO)** or **Soft Actor-Critic (SAC)**, which are advantageous because RL can discover non-intuitive maneuvers. An **Alternative** is **Model Predictive Control (MPC)** with learned dynamics.
*   **Training:** The model must be trained in simulated scenarios using various initial conditions.
*   **Simulation Context:** DL techniques, especially combined with navigation filters like the Extended Kalman Filter (EKF) and geometrical optimization like Perspective-n-Point (PnP), are essential for achieving robust pose estimation and continuous smooth consistency in relative navigation. Recurrent Neural Networks (RNNs) like LSTM are specifically highlighted for processing continuous streams of images in navigation systems.

#### 5. ML Model Reconsideration and Optimization

The development plan explicitly includes a phase for **ML Model Optimization** (Phase 6), acknowledging the need to reconsider models and tune metrics.

**Model Selection Reconsideration**:
*   **Trajectory Prediction:** Compare LSTM vs. Transformer vs. hybrid models. Evaluate **Physics-Informed Neural Networks (PINNs)** as an alternative.
*   **Anomaly Detection:** Primary is the **Variational Autoencoder (VAE)**, which is good for unsupervised learning by learning the normal distribution of telemetry data.

**Efficiency Metrics to Optimize**:
1.  **Inference Speed:** Target $<100\text{ms}$ for trajectory prediction.
2.  **Memory Usage:** Target models $<500\text{MB}$ for deployability.
3.  **Accuracy:** Target position error $<1\text{km}$ at a $24$-hour prediction horizon.

**Optimization Techniques**:
*   Model quantization (INT8)
*   Pruning unnecessary layers
*   Knowledge distillation (teacher-student)
*   Batch inference for multiple satellites
*   GPU acceleration with CUDA

### Step-by-Step Development Plan

The approach favors beginning with **Jupyter Notebooks** to sketch the idea, explore data, and validate challenges simultaneously with application development.

| Phase | Steps (Key Tasks) | Output/Goal |
| :--- | :--- | :--- |
| **Phase 1: Foundation & Data Exploration** (Week 1-2) | 1. Environment Setup (Python/Vite/DB). 2. Data Acquisition: Fetch TLE, SpaceX data, store in `data/raw/`. 3. Coordinate System Implementation (ECI, ECEF, Topocentric) and validation using `skyfield` in `02_coordinate_systems.ipynb`. | Validated coordinate transformations, initial data stored. |
| **Phase 2: Orbital Mechanics & Simulation** (Week 3-4) | 4. Orbital Propagation: Implement SGP4 propagator and perturbation models (J2, atmospheric drag) in `03_orbital_mechanics.ipynb`. 5. Backend Core Development: Implement coordinate system classes, orbital engines, and database models in FastAPI. | Functional SGP4 propagation and core coordinate API endpoints. |
| **Phase 3: Machine Learning Models** (Week 5-6) | 6. Model Development: Train models for Trajectory Prediction (LSTM/Transformer), Anomaly Detection (VAE), and Course Correction ($\Delta V$ optimization using RL/PPO) in `04_model_training.ipynb`. 7. Model Integration: Test models, optimize inference speed, export models, and create model serving endpoints. | Trained ML models integrated into backend services. |
| **Phase 4: Backend API Development** (Week 7-8) | 8. RESTful API: Implement robust endpoints for Satellite Management, Coordinates, Telemetry, Predictions, and Maneuver Optimization. 9. WebSocket Implementation: Set up live telemetry streaming, position updates, and anomaly alerts. | Full functional backend API ready for frontend consumption. |
| **Phase 5: Frontend Development** (Week 9-10) | 10. $3D$ Visualization: Develop `Globe3D.jsx` using Three.js for visualization of Earth, orbits, and real-time satellite positions. 11. Mission Control Interface: Build components like `CoordinateSystemSelector.jsx`, `TelemetryPanel.jsx`, and `CourseCorrection.jsx`. 12. Integration & UX: Connect frontend components to the backend API and WebSockets. | Fully interactive Mission Control Interface. |
| **Phase 6: ML Model Optimization** (Week 11) | 13. Model Performance Tuning: Optimize models for inference speed, memory usage, and accuracy targets (e.g., $<1\text{km}$ error at $24\text{h}$) using quantization and pruning. 14. Model Monitoring: Implement tracking for prediction accuracy and automatic retraining triggers. | Optimized and benchmarked ML models. |
| **Phase 7: Testing & Deployment** (Week 12) | 15. Testing: Conduct unit tests (for coordinates), integration tests (for API), load tests (for WebSockets), and ML model validation tests. 16. Docker & Deployment: Finalize `docker-compose.yml` for deploying the full stack (PostgreSQL/TimescaleDB, backend, frontend, Nginx). | Production-ready, tested application deployed via Docker. |