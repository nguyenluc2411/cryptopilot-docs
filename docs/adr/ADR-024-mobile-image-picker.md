# ADR-024 — Mobile image and video picker for community posts

**Status:** Accepted for the mobile app (FE owner, 2026-11-20); team review pending
**Date:** 2026-11-20
**Deciders:** FE
**Related:** ADR-023; CURRENT_STATE D-160, A-66, Q-97; T-135; SRS 3.7.2 (SCR-26), BR-43, BR-44; D-98

## Context
A-66 brings writing and editing community posts (SCR-26) to the mobile app. A post carries up to four
images or one video (BR-44, a video only on a plan with video posting, BR-43). The backend signs an
upload form (`POST /media/upload-signature`, D-98); the client posts the file straight to the media
storage and names its `publicId` in the post, as the web does. ADR-023 gives the app no way to pick a
photo or a video from the phone.

## Decision
The mobile client adds `image_picker` (Flutter team, flutter.dev; 1.2.4 when added) for T-135, to pick
images (several at once) and one video from the gallery or the camera. On Android 13 and later it uses
the system photo picker, so the app asks for no storage permission. The file goes to the storage with
a plain `Dio` that carries none of the app's tokens; the app's API client is never pointed at the
storage. The same picker serves the journal chart image once Q-97 is answered.

## Consequences
One more package maintained by the Flutter team. The photo picker keeps the app free of broad media
permissions on current Android. Uploads leave the backend's path, so a storage refusal is the file's
(MSG32) and the backend checks the stored file before attaching it.
