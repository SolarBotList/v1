# SolarBotList V1

V1 of SolarBotList


## Structure
/ - Configurations, .ENVs, Main App  
/static - CSS Files, Static Files  
/templates - HTML/Jinja2 Files

This Repository, despite being openly readable is not meant to be redistributed, cloned or self-hosted.  
I have not tested this System in Production.

If you want to self-host anyways, follow the following instructions:

* Import `actress.inst` to actress  
* Create a .env-File with the keys `TOKEN`, `CLIENT_ID`, `CLIENT_SECRET`, `OAUTH_URL` and `REDIRECT_URI`  
* Change all 127.0.0.1's to your actual Server IP  
* Set the App's secret Key (`app.config["SECRET_KEY"] = "..."`)  
* Run this line of code: `python3 -c 'from app import db; db.create_all(); db.session.commit(); exit(0)'`  
