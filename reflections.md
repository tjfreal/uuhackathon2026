# U of U Hackathon Reflection Notes

Written by TJ 2026-04-20 with organization and corpus curation assistance by Claude Code

## Motivation

I was motivated to participate in the hackathon by an interest in AI and what it means for higher education, libraries, society, and individuals alike. Also, I had a backlog of projects that I thought might be viable candidates for a hackathon contribution.

It takes a fair few tokens to build context, make a plan, execute that plan, reflect on what was done, and then decide next steps. I do this day-to-day on my own tasks, but I typically use enough tokens that I can't just build one project after another, one iteration after another. After day 1 of the hackathon I realized that the API usage I used was so minimal, that I was probably working at the wrong scale. When the deadline was extended on Saturday, I think right after I had submitted my first submission iteration, I had some time to think about what to do next. I went on a hike with some close friends and spent time in the wilderness, and came back Saturday night with the decision to take another pass. I had projects that would benefit from API calls to vision, embeddings, and chat models that could still lead to useful local tooling. So I spent my Sunday tinkering.

I keep a daily notes habit that helps me organize and build relevant context for things I want to build, so by the third day I had sort of figured out how to connect those notes with the hackathon in a way that felt safe. I try to build graduated trust in my projects so I feel confident that I'm not oversharing while also not hiding what it is I'm trying to do. It's a delicate balance, and sometimes it makes me tired, but overall I try to have fun and push myself towards growth.

Anyway. I wanted to build something that compounds over time. I don't know if I did that, but I explored it. I thought about it. And I had fun.

## Eddies

I found myself running in circles in a few places, depleting time and energy but not moving anything forward. During ideation, I took my time in finding scope and viable build candidates. I like to just build everything and see what works and what doesn't, but that leaves a lot of cruft and ambiguity. On day three, having built the 8 candidates, I still wondered "is this actually helping or am I just making noise" (referencing lyrics to a wonderful song by Ulver called Nowhere/Catastrophe). In the end we're all just making noise, so I didn't let the question slow down the submission.

Another eddy would have been the decksmith project. I was still just playing around with the tooling at this point, and didn't really go back and refine what I started out to do. I was delighted at what was built, and will certainly pick this one back up at some point, just for funsies.

A little energy went towards figuring out how to build faster. Spawning multiple agents, running into API rate limits, and scoping out longer-form projects took me a hot minute. I like to build from the CLI, so all of this was done just with Codex command line. I know I could do a lot of things a lot better with desktop apps, tools, and integrations, and I'm not opposed to all that, but building at the CLI feels good for me. It comes at the cost of not having the benefits of a more well-rounded tool, but given enough time I'd be dabbling further into those rabbit holes as well.

Finally, I spent a fair bit of time sort of meandering around the concepts of building useful tools and building things that are presentable. A lot of the notes corpus tooling isn't very interesting absent the notes they work on. Getting the tools built in a way that can easily be ingested by my notes tooling took a few tries to figure out. The md files spread throughout the repo are a take on relieving this tension: keep different contexts for different purposes, and keep them updated throughout a project so the story is preserved, the why is preserved, and the how is preserved. Sort of related to this was the confidence gap between starting the process of building and trusting the process of building. After three days it still feels like first-run energy.

## What carries forward

The agents.md-as-brief pattern, presentation.md as story, roadmap.md as build artefact, learnings.md to capture what was learned along the way... each of these are helpful conventions for me moving forward. It's also possible that some of the notes corpus tooling works in a cyclic fashion to refine better contexts and then create better outputs in the next iteration.

The knowledge-work loop structure that flows through items in the repo might be useful going forward. It will take me more time to fully ingest and test and refine them, but I will keep going here. The tools built: signal, throughline, trails, and askme, form a loop that generalizes to other domains. Capture stays free-form, structure is derived from what was captured, idea development and lineage is surfaced, missing areas are sought out, and the system asks questions to stimulate new capture. This isn't a tried and tested loop, more just a toy I am testing out the fun-ness of. 

Sanitation conventions discovered during the hackathon will be useful for me going forward. I tend to wear my heart on my sleeve, so I don't mind being a little vulnerable, but I might feel embarassed by being too-seen, so I spent some time sort of hiding the nature and character of my notes corpus. The tooling sits adjacent to the corpus, but it also suggests things about the corpus. I spent a fair bit of time thinking through how and when to sanitize. I probably did a bad job, so don't go finding out deep dark secrets about me now. Thanks!

## Flywheel stuff

This hackathon felt like a getting started. If we were to go again, I would probably want to start breaking APIs immediately so I could ask for help early instead of eddying. I spent a lot of time context-making this time around, and that context carries forward.

The repo README names a build method that I would start back with: find the question behind the project idea, reduce it to the smallest legible artifact, preserve learnings as durable handoff material, build explanation alongside the thing, allow one project to create structure for the next. Project patterning matters a lot, and everyone needs to practice. Future builds benefit from the context preloading that happened at an earlier build, and mechanisms for storing and forwarding that information are becoming visible. There's a ton still to do here. 

This to-do work also bleeds over into library and information work. Finding aid generators like the topolski-explorer grapple with how to go from a folder of images to something queryable. Future knowledge work includes building these systems, but also building the human understanding to bring these systems to users that want them. 

## Not nearly done

The ladder project in the repo didn't really quite become what I had though. I have a vision of libraries as ladders. No matter who you are or what your education level, the library should be a place where you can reach for the next rung in your education journey. What ended up being built was related, but not big enough in scope. What was built was more about how to build learning content for different audiences. Interesting work, sure, but not ambitious enough. I need all this stuff to cook longer.

## Final thoughts

I had fun. Thanks for the good time. I'd like to see wayyyy more people participating next time. There are brilliant people at the U of U, and getting more of them invested in trying out new workflows would be worthwhile.

-tj





 
