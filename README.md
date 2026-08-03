# Litbrown Creator Assistant (LCA)

*Automation Software for Magic: the Gathering Online&trade; Content Creators*

(screenshot)

## Purpose

Machines are meant to work so humans can play. To this end, The Litbrown Creator Assistant is intended to be the end-all-be-all automation solution for Magic: the Gathering Online&trade; content creators. Its wide variety of features are custom-tailored to remove the time-comsuming tedium and monotony from the MTGO content creator's workflow. Thus, LCA helps creators produce more and higher-quality content, while freeing up their time so they may better pursue the creative side of their work.

## Features

*LCA is a work in progress; many of these features have not yet been implemented!*

### Content Organization

(screenshot)

- Organize your content by series – Leagues, Set Reviews, Paper Gameplay, and whatever else you can think of
- Apply different rules to different content series – how to generate titles and descriptions, who to publish the content to, etc

### Livestream Scheduling

(screenshot)

- Schedule your livestreams in one place
- Automatically mirror those livestreams across Youtube, Twitch, and Patreon
- Automatically advertise those livestreams on multiple platforms, including X/Twitter, Bluesky, and more

### Multicast Management

(screenshot)

- Simultaneously record and stream to one or more streaming services
- TODO

### Automated Video Editing, Rendering, and Publishing

(screenshot)

- TODO

### Assisted Thumbnail Generation

(screenshot)

- TODO

## Get Started

*LCA will eventually feature a single downloadable .exe file that will handle all these steps for you. But for now...*

You will need to install the following software:
- Git: https://git-scm.com/install/
- UV: https://docs.astral.sh/uv/getting-started/installation/

Once you have installed these dependencies, it's time to download LCA. Open a terminal in an empty directory, then run the following command:

```
git clone https://github.com/FatesealMagic/Litbrown-Creator-Assistant.git .
```

Once the download is complete, you can run LCA with the following command:

```
uv run -m source
```

The first launch may take some time, since UV has to download project dependencies.
