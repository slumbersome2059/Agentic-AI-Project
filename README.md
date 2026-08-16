# Running Route Generator using Agentic AI
### Description / Overview
This is a weekend project that I did to create a random running route generator as part of an introduction bootcamp to our Computer Science course at the start of the academic year. The project guidelines were to use Agentic AI and they were happy with using a lot of AI generated code to design the app given the short timeline . 
### Demo


![[Screenshot from 2026-08-16 15-36-05.png]]
Route Output:
Starting route generation for BN6 8LP and 2.0km.
Geocoded BN6 8LP to (50.922115, -0.1379842)
Shortest length is 591.6365741879973
total length 1890.1105194313523
Generated route with 37 points.
Starting from the first coordinate, head north on unnamed street for approximately 39 metres, then turn slightly north-east and continue for approximately 36 metres. Next, turn east onto Dale Avenue and continue for approximately 81 metres. Then, turn north-east onto Highlands Close and continue for approximately 48 metres. Afterward, turn east onto Willowbrook Way and continue for approximately 427 metres. Then, turn south-east onto unnamed street and continue for approximately 30 metres. Afterward, turn north-east onto Willowbrook Way and continue for approximately 48 metres. Then, turn east onto unnamed street and continue for approximately 122 metres. 
....(rest of response cut for space but it basically gives you the route, the full text can be viewed in output.txt)
## Usage
- Clone this repository
- Navigate to the repository on the command line
- Add an environment variable with your gemini api key so the format should be GEMINI_API_KEY='your key' 
- You can create a temporary key by doing export GEMINI_API_KEY='your key'
- Run `$ source .venv/bin/activate` on the command line 
- Run `$ python3 routeGen.py`
- Leave this running and on a new terminal run `$ python3 -m http.server 8000`
- Open your web browser and go to http://localhost:8000/ where you can use the program
## Features
- Route generated on map using networkx algorithms
- A full description of the route is given by using gemini flash. This helped me learn about prompt engineering and a few useful things I could do like giving a system instruction. 
- In the future, I plan to add the functionality of playing the route on audio depending on your location
- In the future, I would like to add tool use and make it so that the route is generated using gemini as well
## Tech Stack / Built With
- Languages: Python, HTML, CSS, JS
- Frameworks: networkx, osmnx, flask
