# Trendy

**One picture a day of what the world is talking about.**

👉 See the gallery: [artemgalimzyanov.github.io/trendy-nft](https://artemgalimzyanov.github.io/trendy-nft/)

## The idea

We are surrounded by daily news and endless noise. Often, consuming the news leaves us feeling distressed, sad, or angry. Sometimes, we check the news so frequently that it becomes almost addictive.

The aim of this app is to transform each day’s top global stories into a single, hand-drawn-style cartoon, presenting the news in a friendlier and more approachable way.

To preserve each day’s artwork, decentralized storage was chosen. Each image is stored as a permanent record and will remain available even if the front end disappears.

The pictures form a series featuring recurring characters: a curious, ginger-haired boy who lives with his eccentric grandparents in a slightly shabby English country house. The visual style was inspired by a recent visit to London, when I was walking through Kensington and came across Annie Tempest’s comic strip Tottering-by-Gently.

Over time, the gallery will grow into a 365-day calendar of world news, with one cartoon for each day. Every image includes NFT-ready metadata, allowing any day’s artwork to be minted as an NFT in the future.

## How it works

The pipeline runs automatically once a day:

```
world news → top 5 topics → cartoon scene → image prompt → AI image → IPFS → gallery page
```

1. **Get the trends.** Headlines are collected from about 20 news outlets across North
   America, Europe, the Middle East, Asia, Africa, Latin America and Oceania. A small
   language model picks the 5 stories that the most outlets are covering, so no single
   country or outlet sets the agenda.
2. **Write the scene.** Each topic becomes one short action for the cartoon cast. The boy
   acts out the top story, two household members act out the next two, and the rest show up
   as small props in the background.
3. **Build the prompt.** The actions are combined with a fixed description of the hero,
   the house and the art style, so every day looks like part of the same series.
4. **Generate the image.** An AI image model draws the cartoon. A small JPEG copy is made
   for storage and the web.
5. **Store it.** The image is pinned to IPFS (decentralized storage). Then a metadata file
   (date, trends, image link) in the ERC-721 NFT format is pinned there too.
6. **Publish.** The day is added to the gallery, a static page on GitHub Pages that shows
   a grid of days. Click any day to see the full picture, its trends and its IPFS links.

## What's next

- **Minting.** The metadata already follows the NFT standard, so the next step is to mint
  each day's picture on a blockchain.
