# Trendy

**One picture a day of what the world is talking about.**

👉 See the gallery: [artemgalimzyanov.github.io/trendy-nft](https://artemgalimzyanov.github.io/trendy-nft/)

## The idea

Every day the news is full of big, loud and often heavy stories. Trendy turns each day's top
global stories into a single hand-drawn style cartoon, and puts that cartoon on decentralized
storage so it stays around as a permanent record of the day.

The pictures are a series with recurring characters: a curious ginger-haired boy who lives
in a slightly shabby English country house with his eccentric grandparents, a weary butler,
a gardener and two overweight dogs. Every day the household hears the world news and acts it
out at home with toys, garden tools and teacups. The style is a classic British newspaper
cartoon: wobbly ink lines, soft watercolour, gentle humour. Real people show up only as
symbols or props, and sad events are drawn quietly and with care, never as a joke.

Over a year the gallery grows into a 365-day calendar of the world's news, one cartoon per
day. Each picture comes with NFT-ready metadata, so any day can be minted as an NFT later.

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
   (date, trends, prompt, image link) in the ERC-721 NFT format is pinned there too.
6. **Publish.** The day is added to the gallery, a static page on GitHub Pages that shows
   a grid of days. Click any day to see the full picture, its trends and its IPFS links.

## What's next

- **Minting.** The metadata already follows the NFT standard, so the next step is to mint
  each day's picture on a blockchain (starting with a testnet).
- **More sources.** Trends could also come from social media, not just news outlets.
