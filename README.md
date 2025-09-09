**WORK IN PROGRESS**

**Full-stack live-ops dashboard** that uses machine learning techniques like Multi-Armed Bandit (MAB) to automate and optimize A/B testing of in-game content like FTUE (first time user experience / tutorial) variants. 

The tool allows a user to set up content variants, create a new campaign, and then run simulations of various machine learning algorithms to optimize metrics like click through rate. The app also allows for the definition of user segments and true click-through rates. 

**Frontend:** React, Vite, Tailwind CSS, Recharts

**Backend:** Python, FastAPI, SQLite

**ML Algorithms:** Multi-Armed Bandit (MAB), Segmented MAB, Contextual MAB with LinUCB

The app is built to work in simulation mode, so all the incoming 'player' requests and impressions are simulated. There is also an API mode so real products could easily hook into the program. 

<img src="https://github.com/cbpalumbi/liveops-dashboard/blob/main/readme_images/frontend.PNG?raw=true" width="500px"/>
<img src="https://github.com/cbpalumbi/liveops-dashboard/blob/main/readme_images/simulation.PNG?raw=true" width="500px"/>
<img src="https://github.com/cbpalumbi/liveops-dashboard/blob/main/readme_images/db.PNG?raw=true" width="500px"/>
