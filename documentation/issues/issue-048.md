# Issue #48: Support for Japanese Chart Symbols

**Status:** OPEN
**Created:** 2022-08-29T15:37:51Z
**Updated:** 2022-09-08T21:01:00Z
**Labels:** None
**URL:** [https://github.com/terriko/pyknit/issues/48](https://github.com/terriko/pyknit/issues/48)

## Description

I am delighted to find this open-source project! Python is not a language I often code in, but I will attempt to provide support for this issue myself. Any help on it or if someone can easily add this feature - that would be greatly appreciated.

I enjoy the charting feature as demonstrated by the [Cabled Cowl demo](https://github.com/terriko/pyknit/blob/main/documentation/CowlCable.ipynb) and I noticed thanks to another issue listed that the chart symbols were pulled from this site by the Craft Yarn Council - [Site Link](https://www.craftyarncouncil.com/standards/knit-chart-symbols).

That site does show the Japanese symbol alongside an 'other' set, but this project currently supports only the 'other' set of symbols. I'd love the stitch legend import to support both types of symbols, perhaps creating a toggle on which ones to use. I was thinking that the 'other' symbols could remain the default, and a command could be used such as
`stitch legend = setStitchLegend(Japanese)`
(Forgive my Java accent :) )

An alternative method would be to create a duplicate that could be imported instead of **stitch_legend**, called **stitch_legend_japanese**. I'm not sure which would be an easier or cleaner implementation yet, as I haven't dived into the code.

I am very fond of Japanese Knitting Charts and use them almost exclusively. I would heavily use pyknit to convert verbal instructions I found into a Japanese chart given the opportunity! I think this software has amazing potential for a code savvy knitter, and I'm looking foward to using it more.

---

## Branch
Work on this issue using the branch: `issue-48`

```bash
git checkout issue-48
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/48)
