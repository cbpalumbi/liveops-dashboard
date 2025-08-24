Full-stack, liveops dashboard that uses machine learning techniques like Multi-Armed Bandit (MAB) algorithm to automate and optimize A/B testing of in-game content like ad banners. 

The tool allows a user to upload multiple banner versions, create a new campaign, and then run simulations of various machine learning algorithms on metrics like click through rate. The app also allows for the configuration of user segments and true CTRs. 

Frontend: React, Vite, Tailwind CSS, Recharts
Backend: Python, FastAPI, SQLite
ML Algorithms: Multi-Armed Bandit (MAB), Segmented MAB, Contextual MAB with K-means clustering 

The app is built to work in simulation mode, so all the incoming 'player' requests and impressions are simulated. There is also an API mode so real products could easily hook into the program. 


**User Story**

As a game liveops analyst,

I want to set up a simulated audience with specific demographic and behavioral distributions,
so that I can evaluate how different ML techniques (MAB, contextual bandits, etc.) optimize banner CTR in scenarios that resemble my real or hypothetical player base.
