**WORK IN PROGRESS**

**LiveOps Optimization Dashboard: Multi-Armed Bandit A/B Testing Platform** 
This project is a full-stack, end-to-end LiveOps dashboard designed to automate and optimize the decision-making process for in-game content releases. It is intended to be a data sandbox and a demonstration of how machine learning (ML) can improve upon manual A/B testing, driving superior business outcomes like higher tutorial completion rates.

The tool allows a user to set up content variants, create a new campaign, and then run simulations of various machine learning algorithms to optimize tutorial completion rate.

The platform dynamically allocates traffic to the best-performing content variants as the simulation progresses, focusing on the core Multi Armed Bandit principle of exploration vs. exploitation.

**Frontend:** React, Vite, Tailwind CSS, Recharts

**Backend:** Python, FastAPI, SQLite

**ML Algorithms:** Multi-Armed Bandit (MAB), Segmented MAB. Algorithms implemented from scratch in Python (no machine learning libraries).

**Key Features and Capabilities** 
- Dynamic Campaign Management: Users can configure and launch new optimization campaigns, defining content variants, setting simulation parameters, and specifying ground-truth performance.

- Automated Optimization Strategies: The tool implements and visualizes the performance of two distinct machine learning strategies:
    - Standard Multi-Armed Bandit (MAB): Dynamically identifies and exploits the single highest-performing content variant.
    - Segmented MAB: Applies unique MAB policies to distinct, user-defined segments (e.g., region, platform), each with modifiers to tutorial completion rate, maximizing performance across a heterogeneous user base.
- Data-Driven Visualization: A modern frontend provides a clear, real-time dashboard view of campaign performance, showing variant traffic allocation, cumulative rewards, and overall metrics.
- API-First Design: The simulation engine is built with an API-first approach, allowing for easy extension into a production environment where real-world products could hook into the platform's decision-making service.


<img src="https://github.com/cbpalumbi/liveops-dashboard/blob/main/readme_images/tutorials.PNG?raw=true" width="500px"/>
<img src="https://github.com/cbpalumbi/liveops-dashboard/blob/main/readme_images/config.PNG?raw=true" width="500px"/>
<img src="https://github.com/cbpalumbi/liveops-dashboard/blob/main/readme_images/graphs.PNG?raw=true" width="500px"/>
