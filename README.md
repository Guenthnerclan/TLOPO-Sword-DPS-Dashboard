# TLOPO-Sword-DPS-Dashboard
Python and exe files for creating a dashboard to anaylze damage per second on varies swords in TLOPO

## Accessing the Dashboard

1. If you're on windows (and maybe mac and other systems), you can download the exe file which will easily run the dashboard. When run, it opens a console window and a new tab on a browser to a dash app server run locally by you through the executable file. When you're done, just close the tab and close the console to end the server.
2. If you have python setup on your computer you can run the python file instead with the same outcomes, though you may need to install some packages first.
3. There is also a jupyter lab notebook that can be run producing a dashboard app within jupyter lab.

## The Dashboard Itself

It presents two graphs for easy side-by-side comparisons. Each graph plots the DPS, explained in the next section, versus time. To manipulate the graphs you have four sets of information to change.
1. Each graph has a dropdown to select the weapon(s) to graph
2. Each also has checkboxes that when checked indicate you will forgoe having that attack in your combo. E.g. checking skip 3 and skip 4 will only have a sword combo with the first two attacks and the final 5th attack.
3. There is a dropdown affecting both graphs for the level of the enemy to simulate fighting. This only creates minor changes.
4. There is a slider to indicate the start and end points for both graphs. You could also interact directly with the plots and zoom in, select regions, etc. without needing to use the slider at all.

## Understanding This Data

This tool is used to analyze the effectiveness of weapons falling under the weapon type of swords in the game The Legend of Pirates Online. It is important in the game to do as much damage as quickly as possible, thus using the best weapons in the right ways is key. Each sword generally does a basic 5 attack chain, one after the other, resetting when the last is performed. There is an additional attack on all swords and some have a special skill that can be put to use. The main value to assess the "effectiveness" of swords is "DPS", short for "damage per second". This measures the rate that damage is being output, which again the higher the better. More nuanced information and analysis of results can be found here: https://tlopocommunity.com/index.php?threads/ned-reddavis-guide-to-the-strongest-swords-pyp-v1-7-5.79/. However, this is enough to make use of the dashboard and see which weapons perform better or worse under what conditions via the DPS value.
