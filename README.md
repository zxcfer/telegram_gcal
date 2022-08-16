# rsstgbot

* run `pip install -r requirements.txt`
* then run `python bot.py` to start the telegram bot
* run `python server.py` to start the backend server
* use the telegram command `/auth` to verify the google calender
* to add an event run `/schedule {Event Title} {Date}`

```
/schedule Feed the cat tomorrow
/schedule Feed the dog 30 May 11am-12pm
```

setup webhook

```
https://api.telegram.org/bot[TU_TOKEN]/setWebhook?url=https://[TU_DOMINIO]/[CAMINO_AL_WEBHOOK]
```

https://api.telegram.org/bot5758197113:AAHH4J_2fdZi88TtfMYFK3kxxxA2f7-2v2M/setWebhook?url=https://scheduler.f21.app/