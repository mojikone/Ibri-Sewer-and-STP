---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Two problems with the SewerGEMS 10.4 model I'm driving through the OpenFlows API. 1) I added year alternatives for 2036 and 2041 with Add(parent) under the loaded sanitary-load alternative; 2036 works but 2041 can't be read back and comes out empty. 2) My own Python sizing (Colebrook-White, ks 1.5 mm, d/D 0.65/0.50, Table 11 gradients) gives about 60 pipes one size smaller than SewerGEMS's own design, mostly DN315 to 280 and DN500 to 450, and for a handful of the biggest trunks my code says no size fits. What's going on and what do I change? Put the answer in answer.md.
