---
layout: default
published: true
title: Customize split images
nav_order: 4
---

<link rel="stylesheet" href="css/main.css">

# Customize Split Images

Each split image's settings can be individually set by editing the image's filename. Desired settings values are placed between underscores: `_x_`.

Here is an example of a customized split image:

{: .example }
`001_mysplit_[5]_{b}_(85).png`<br>  
`(85)` The video must match at least 85% of the split image  
`{b}` Don't split until the match percent goes above 85% AND drops back below 85%  
`[5]` Don't start comparing the NEXT split image until 5 seconds after splitting

{: .tip }  
Custom split settings don't need to be listed in any particular order.

## Threshold

Override the [default threshold]({% link 04-settings.md %}#default-threshold) for this split.

The value is inserted between parentheses: `(value)`.

{: .example }
`001_mysplit_(95).png` The split's threshold is 95%.

## Delay

Override the [default delay]({% link 04-settings.md %}#default-delay) for this split.

The value is inserted between pound signs: `#value#`.

{: .example }
`001_mysplit_#5#.png` The split's delay is 5 seconds.

## Pause

Override the [default pause]({% link 04-settings.md %}#default-pause) for this split.

The value is inserted between brackets: `[value]`.

{: .example }
`001_mysplit_[120].png` Don't look for the next split image for 2 minutes after this split.

## Loops

Force a split to loop. Useful if consecutive splits use the same image.

Insert the value between "at" signs: `@value@`.

Default: `1`

{: .example }
`001_mysplit_@2@.png` The split will be used twice instead of once.

# Special Split Types

You can tell Pilgrim Autosplitter to do special actions when matching a split. 

Specify a special split type by inserting its corresponding letter between curly braces: `{value}`. 

{: .note }
Special split types can be used together, but the dummy type `{d}` will always override the pause type `{p}`.

## Pause type

Force Pilgrim Autosplitter to press the [pause hotkey]({% link 04-settings.md %}#pause-timer) instead of the [split hotkey]({% link 04-settings.md %}#start--split) when splitting. 

Insert a `p` between curly braces: `{p}`.

{: .example }
`001_mysplit_{p}.png` Press the pause hotkey instead of the split hotkey when a match is found.

## Dummy type

Force Pilgrim Autosplitter NOT to press a [hotkey]({% link 04-settings.md %}#hotkeys) when splitting.

Useful if you rely on a certain image to know a split is coming, but you don't want to split ON that image.

Insert a `d` between curly braces: `{d}`.

{: .example }
`001_mysplit_{d}.png` Do nothing when a match is found.

## Below type

Force Pilgrim Autosplitter to wait to split until the video has matched the [threshold](#threshold) AND dropped back below it.

Insert a `b` between curly braces: `{b}`.

{: .example }
`001_mysplit_{b}.png` After finding a match, wait until the video no longer matches before splitting.
