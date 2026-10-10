I planned and researched the project in a separate normal chat. I 

built a good CLAUDE.md from the start so Claude had most of the context

and rules beforehand. This allowed Claude to work systematically through everything

with only a few directions


One thing that shaped the project from the beginning was the "week" definition.

The problem statement says "10th week" without defining it, and by 19th October

most teams had played 12 to 14 games. I defined week N as 7-day blocks

from 17 August and added --season-start and --until so the result doesn't depend

on the input file


Claude asked how to build the test fixtures, and I chose to give it the official standings 

instead of letting it generate and freeze its own output, because a test built from the code’s own 

output proves nothing.


I collected the raw data myself by copying it from the official site, and caught a wrong date on one 

line (25 Oct that should have been 5 Oct).

I also compared week 5 and week 10 output with the official tables



Claude wrote most of the code with few prompts. What I learned was that

a strong starting point makes a big difference. A detailed CLAUDE.md with enough context kept Claude on 

track, especially the known pitfalls, like developing on Windows while the target machine is Unix


One thing I could do differently is perhaps prompt more and push back on Claude’s design choices

so I understand why it chose a structure instead of just accepting it.