# Annke Security Notification App

An attempt at integrating my Annke home-security system with some custom monitoring and ML tools.

## Rationale
The emails from my Anker system were not overly helpful - there are many, many irrelevant motion detections (~100/day) and there is no visual content on them to show me if there's anything I should be worried about.

My DVR is stored externally, so I don't have easy access to the raw machine.

I wanted to build an app that would allow me to stream the relevant info to a host machine, and eventually I'd like to run some computer vision workloads over it for basic annotation (i.e. I'll throw YOLO at it and see what comes out!).

## How it works
Currently works by checking an IMAP inbox that is only used for the DVR notifications. It queries the inbox for any unread messages matching the DVR's subject pattern and pulls them down to the host. It then parses each of the emails, extracts the notification type, camera and date/time information then uses that to capture an RTSP feed from the DVR containing a short clip of the event.

I'm using coroutines (`asyncio`) and `multiprocessing` to periodically poll the email server, then a pool of processes will stream the RTSP feeds in parallel.


## Known issues
Many. Some of the bigger ones:

* When an RTSP feed fails to create, it just crashes the app. The failure should be caught and the events added to a backlog for streaming later.
* Setting the parallel processes too high results in the system not having enough bandwidth for the RSTP feeds, which then crashes the app due to the above. A short-term fix for this is to swap to the lower-res secondary stream.
* When multiple cameras pick up the same event (in the same notification), we open two streams and dumbly concatenate them horizontally. This exaccerbates the above.
* After writing all the code to handle the emails, I discovered the [hikvision-client](https://github.com/MissiaL/hikvision-client/) Python package. This should let me poll the device directly for live events. Email parsing would only be required for retroactive capture.
* The streams are currently only real-time. This seems to be a limitation of RTSP, but it would be nice to speed this up.
* The events don't persist on the host, only the clips.
